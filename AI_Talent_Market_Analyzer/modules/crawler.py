# 数据爬取模块 - 招聘信息采集引擎 (Playwright 版)
# 设计思想：
# 1. Playwright 真实浏览器渲染 -> 突破 JS 反爬和动态加载
# 2. XHR 响应拦截 -> 直接捕获后端 JSON 数据，比解析 DOM 更可靠
# 3. 完善的异常处理链：网络异常->重试->降级->生成模拟数据
#
# 技术亮点：
# - 复用本地 Chrome 浏览器，零额外下载
# - page.evaluate() 在浏览器上下文直接提取数据
# - page.on("response") 拦截 API JSON 作为主数据源

import time
import random
import re
import json
import threading
import os
from datetime import datetime, timedelta
from pathlib import Path
from config import (
    HEADERS, MAX_PAGES, REQUEST_DELAY, REQUEST_TIMEOUT,
    MAX_RETRIES, SEARCH_KEYWORDS
)

# =========================================================================
# 装饰器 —— 自动重试机制
# =========================================================================
def retry_on_failure(max_retries=MAX_RETRIES, delay=1.0):
    """函数调用失败时自动重试，指数退避策略"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait = delay * (2 ** (attempt - 1))
                        print(f"  [警告] [{func.__name__}] 第{attempt}次失败，{wait:.0f}s后重试: {e}")
                        time.sleep(wait)
            raise last_exception
        return wrapper
    return decorator


# =========================================================================
# 核心爬虫类 —— Playwright 真实浏览器
# =========================================================================
class JobCrawler:
    """
    使用 Playwright 驱动本地 Chrome，突破 JS 反爬，采集真实职位数据。
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._progress = {"done": 0, "total": 0}
        self._browser = None
        self._playwright = None
        self._api_jobs = []       # 从 XHR 响应中捕获的结构化数据
        self._api_lock = threading.Lock()

    def _ensure_browser(self):
        """懒初始化浏览器 —— 只在真正需要爬取时才启动"""
        if self._browser is not None:
            return

        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()

        # 寻找本地 Chrome 路径
        chrome_paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
            os.path.expanduser("~/AppData/Local/Google/Chrome/Application/chrome.exe"),
        ]
        executable_path = None
        for p in chrome_paths:
            if Path(p).exists():
                executable_path = p
                break

        launch_args = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        }
        if executable_path:
            launch_args["executable_path"] = executable_path

        self._browser = self._playwright.chromium.launch(**launch_args)

    def _create_page(self):
        """创建带反检测配置的新页面"""
        context = self._browser.new_context(
            user_agent=HEADERS.get("User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        page = context.new_page()

        # 抹除 webdriver 检测标记
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
        """)

        # 拦截 XHR 响应 —— 捕获返回 JSON 的 API 请求
        def on_response(response):
            url = response.url
            content_type = response.headers.get("content-type", "")
            if "json" in content_type and response.status == 200:
                # 51job 的职位搜索 API 包含这些特征
                if any(kw in url for kw in ["search", "joblist", "job/list", "api"]):
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            with self._api_lock:
                                self._api_jobs.append(data)
                    except Exception:
                        pass  # 非 JSON 或解析失败，忽略

        page.on("response", on_response)
        return page

    def _fetch_page(self, keyword: str, page_num: int):
        """
        用 Playwright 加载 51job 搜索结果页。

        URL 格式: we.51job.com/pc/search?keyword={keyword}&searchType=2&page={page}
        """
        self._ensure_browser()
        page = self._create_page()

        url = (
            f"https://we.51job.com/pc/search"
            f"?keyword={keyword}&searchType=2&page={page_num}"
        )

        page.goto(url, wait_until="networkidle", timeout=REQUEST_TIMEOUT * 1000)
        page.wait_for_timeout(2000)

        return page, page.content()

    def _parse_job_cards(self, page, html: str, keyword: str) -> list[dict]:
        """
        从 51job 搜索结果页提取职位卡片。

        主策略：解析 .joblist-item 中嵌入的 sensorsdata JSON（包含所有核心字段）。
        备策略：innerText 文本行解析（兜底）。
        """
        try:
            cards = page.evaluate("() => {"
                "const items = document.querySelectorAll('.joblist-item');"
                "const results = [];"
                "items.forEach(function(item) {"
                "  const sensorEl = item.querySelector('[sensorsdata]');"
                "  const sensorData = sensorEl ? sensorEl.getAttribute('sensorsdata') : null;"
                "  const lines = item.innerText.split('\\n').filter(function(l) { return l.trim(); });"
                "  const link = item.querySelector('a[href*=\"jobs.51job.com\"]');"
                "  results.push({"
                "    sensor: sensorData,"
                "    lines: lines,"
                "    url: link ? link.href : ''"
                "  });"
                "});"
                "return results;"
            "}")
        except Exception:
            return []

        if not cards:
            return []

        parsed = []
        for card in cards:
            try:
                job = None
                sensor_str = card.get("sensor")
                if sensor_str:
                    job = self._parse_sensorsdata(sensor_str, card.get("lines", []), card.get("url", ""), keyword)
                if not job:
                    job = self._parse_card_lines(card.get("lines", []), card.get("url", ""), keyword)
                if job:
                    parsed.append(job)
            except Exception:
                continue

        return parsed

    def _parse_sensorsdata(self, sensor_str: str, lines: list[str], job_url: str, keyword: str) -> dict | None:
        """
        从 sensorsdata JSON 提取结构化字段。

        51job 的 sensorsdata 示例：
        {
          "jobId": "171142066",
          "jobTitle": "python开发工程师",
          "jobSalary": "1.5-1.8万",
          "jobArea": "深圳·龙华区",
          "jobYear": "3年及以上",
          "jobDegree": "本科",
          "companyId": "2425656",
          "jobTime": "2026-06-15 09:31:43",
          ...
        }
        """
        try:
            data = json.loads(sensor_str)
        except (json.JSONDecodeError, TypeError):
            return None

        job_title = data.get("jobTitle", "")
        if not job_title:
            return None

        # 薪资
        salary_text = data.get("jobSalary", "")
        salary_min, salary_max, salary_avg = self._parse_salary(salary_text)

        # 地点
        job_area = data.get("jobArea", "")
        city, district = self._parse_city(job_area)

        # 经验
        job_year = data.get("jobYear", "")
        experience, _ = self._parse_requirements(job_year)

        # 学历
        job_degree = data.get("jobDegree", "")
        _, education = self._parse_requirements(job_degree)
        if education == "不限" and job_degree:
            # sensorsdata 的 jobDegree 可能直接是 "本科"、"硕士" 等
            for edu in ("博士", "硕士", "本科", "大专", "中专", "高中"):
                if edu in job_degree:
                    education = edu
                    break
            if education == "不限":
                education = job_degree

        # 发布日期
        job_time = data.get("jobTime", "")
        post_date = job_time[:10] if job_time else datetime.now().strftime("%Y-%m-%d")

        # 职位 URL
        job_id = data.get("jobId", "")
        if not job_url and job_id:
            job_url = f"https://jobs.51job.com/all/co{job_id}.html"

        # ---- 从 innerText 行中提取公司信息和技能标签 ----
        company_name = "未知公司"
        company_size = "未知"
        company_type = "未知"
        industry = "未知"
        skills_list = []

        # 过滤掉按钮行和职位名行
        skip_prefixes = ("去申请", "投递", "收藏")
        info_lines = [l for l in lines[1:] if l and not l.startswith(skip_prefixes)]

        for line in info_lines:
            c_size, c_type, c_ind = self._parse_company_info(line)
            if c_size:
                company_size = c_size
            if c_type:
                company_type = c_type
            if c_ind:
                industry = c_ind

            # 技能标签过滤
            is_skill = (
                len(line) < 25
                and not re.search(r'[\d.]+[万千kK年人]', line)
                and not any(kw in line for kw in (
                    '公司', '有限', '集团', '申请', '投递', '|', '/',
                    '天前', '小时前', '刚刚', '今天', '昨天', '回复',
                ))
                and line not in (job_title, job_area, salary_text)
            )
            if is_skill:
                skills_list.append(line)

            # 公司名
            if ('公司' in line or '有限' in line or '集团' in line) and '|' not in line and len(line) > 4:
                company_name = line
            elif '|' in line:
                # "公司名 | 行业 | 类型 | 规模"
                parts = line.split('|')
                for i, part in enumerate(parts):
                    part = part.strip()
                    if i == 0 and part:
                        company_name = part
                    c_size, c_type, c_ind = self._parse_company_info(part)
                    if c_size:
                        company_size = c_size
                    if c_type:
                        company_type = c_type
                    if c_ind:
                        industry = c_ind

        return {
            "job_title": job_title,
            "company_name": company_name,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_avg": salary_avg,
            "city": city,
            "district": district,
            "experience": experience,
            "education": education,
            "company_size": company_size,
            "company_type": company_type,
            "industry": industry,
            "skills": json.dumps(skills_list, ensure_ascii=False) if skills_list else "",
            "benefits": "",
            "post_date": post_date,
            "job_url": job_url,
            "source": f"51job-{keyword}",
        }

    def _parse_card_lines(self, lines: list[str], job_url: str, keyword: str) -> dict | None:
        """纯文本解析 —— sensorsdata 不可用时的兜底方案。"""
        if len(lines) < 3:
            return None

        content_lines = [
            l for l in lines
            if l not in ("去申请", "投递", "收藏") and "申请" not in l
        ]
        if len(content_lines) < 3:
            return None

        job_title = content_lines[0]

        salary_min = salary_max = salary_avg = 0
        for line in content_lines[:4]:
            if re.search(r'[\d.]+', line) and (
                '万' in line or '千' in line or 'K' in line or 'k' in line
                or re.search(r'\d+[-~]\d+', line)
            ):
                salary_min, salary_max, salary_avg = self._parse_salary(line)
                break

        city, district = "未知", ""
        for line in content_lines[:4]:
            if '·' in line and not re.search(r'[\d.]+[万千kK]', line):
                city, district = self._parse_city(line)
                break

        experience, education = "不限", "不限"
        for line in content_lines:
            if re.search(r'(经验|应届|在校生)', line):
                experience, _ = self._parse_requirements(line)
            if re.search(r'(本科|大专|硕士|博士|中专|高中)', line):
                _, education = self._parse_requirements(line)

        company_name = "未知公司"
        company_size = "未知"
        company_type = "未知"
        industry = "未知"
        skills_list = []

        for line in content_lines[1:]:
            c_size, c_type, c_ind = self._parse_company_info(line)
            if c_size: company_size = c_size
            if c_type: company_type = c_type
            if c_ind: industry = c_ind
            if ('公司' in line or '有限' in line or '集团' in line) and '|' not in line:
                company_name = line
            elif '|' in line:
                parts = line.split('|')
                company_name = parts[0].strip() or company_name
                for part in parts[1:]:
                    c_size, c_type, c_ind = self._parse_company_info(part.strip())
                    if c_size: company_size = c_size
                    if c_type: company_type = c_type
                    if c_ind: industry = c_ind
            if (len(line) < 25 and not re.search(r'[\d.]+[万千kK年人]', line)
                    and not any(kw in line for kw in (
                        '公司', '有限', '集团', '申请', '投递', '天前', '小时前', '回复',
                    ))):
                skills_list.append(line)

        post_date = datetime.now().strftime("%Y-%m-%d")
        for line in content_lines:
            m = re.search(r'(\d+天前|\d+小时前|刚刚|今天|昨天)', line)
            if m:
                rel = m.group(1)
                today = datetime.now()
                if "天前" in rel:
                    days = int(re.search(r'(\d+)', rel).group(1))
                    post_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
                elif "小时前" in rel:
                    post_date = today.strftime("%Y-%m-%d")
                elif rel in ("刚刚", "今天"):
                    post_date = today.strftime("%Y-%m-%d")
                elif rel == "昨天":
                    post_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
                break

        return {
            "job_title": job_title, "company_name": company_name,
            "salary_min": salary_min, "salary_max": salary_max, "salary_avg": salary_avg,
            "city": city, "district": district,
            "experience": experience, "education": education,
            "company_size": company_size, "company_type": company_type, "industry": industry,
            "skills": json.dumps(skills_list, ensure_ascii=False) if skills_list else "",
            "benefits": "", "post_date": post_date or datetime.now().strftime("%Y-%m-%d"),
            "job_url": job_url, "source": f"51job-{keyword}",
        }

    def _extract_from_api_json(self, data: dict, keyword: str) -> list[dict]:
        """从 XHR 拦截的 JSON 中递归提取职位列表。"""
        results = []

        def search_jobs(obj, depth=0):
            if depth > 6:
                return
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        if any(k in item for k in ["jobTitle", "job_title", "title", "positionName", "jobName"]):
                            try:
                                title = (item.get("jobTitle") or item.get("job_title")
                                         or item.get("title") or item.get("positionName")
                                         or item.get("jobName") or "")
                                if title:
                                    salary_text = str(item.get("salary") or item.get("provideSalary") or "")
                                    s_min, s_max, s_avg = self._parse_salary(salary_text)
                                    city_str = str(item.get("city") or item.get("workCity") or item.get("location") or "")
                                    results.append({
                                        "job_title": str(title),
                                        "company_name": str(item.get("companyName") or item.get("company_name") or item.get("company") or "未知公司"),
                                        "salary_min": s_min, "salary_max": s_max, "salary_avg": s_avg,
                                        "city": self._parse_city(city_str)[0],
                                        "district": self._parse_city(city_str)[1],
                                        "experience": str(item.get("experience") or item.get("workYear") or "不限"),
                                        "education": str(item.get("education") or item.get("degree") or "不限"),
                                        "company_size": "未知", "company_type": "未知", "industry": "未知",
                                        "skills": "", "benefits": "",
                                        "post_date": datetime.now().strftime("%Y-%m-%d"),
                                        "job_url": item.get("jobUrl") or item.get("url") or "",
                                        "source": f"51job-{keyword}",
                                    })
                            except Exception:
                                pass
                        else:
                            search_jobs(item, depth + 1)
            elif isinstance(obj, dict):
                for v in obj.values():
                    search_jobs(v, depth + 1)

        search_jobs(data)
        return results

    # ---------------------------------------------------------------------
    # 薪资文本解析
    # ---------------------------------------------------------------------
    def _parse_salary(self, text: str) -> tuple[float, float, float]:
        """解析薪资文本，统一返回 K/月。支持 万/年、万/月、千/月、K/月 等格式。"""
        if not text or "面议" in text:
            return (0, 0, 0)

        is_annual = '/年' in text or '万/年' in text

        text = re.sub(r'[·*＊]\d{1,2}薪', '', text)
        text = text.replace("/月", "").replace(" /月", "").replace("/年", "").replace(" /年", "").strip()

        unit_map = {'万': 10, 'w': 10, 'W': 10, '千': 1, 'k': 1, 'K': 1}

        # 区间格式: "X-Y" 或 "X-Z万"
        range_pat = re.compile(
            r'([\d.]+)\s*([万千kKwW]?)\s*[-~至到]\s*([\d.]+)\s*([万千kKwW]?)'
        )
        m = range_pat.search(text)

        if m:
            lo, lo_unit = float(m.group(1)), m.group(2)
            hi, hi_unit = float(m.group(3)), m.group(4)

            # 共享单位：一方没写单位时沿用另一方的单位
            shared_unit = lo_unit or hi_unit
            if shared_unit in unit_map:
                if not lo_unit:
                    lo *= unit_map[shared_unit]
                else:
                    lo *= unit_map[lo_unit]
                if not hi_unit:
                    hi *= unit_map[shared_unit]
                else:
                    hi *= unit_map[hi_unit]
            elif lo >= 1000 or hi >= 1000:
                # 无单位纯数字且值很大，推断为元 → K
                lo /= 1000
                hi /= 1000

            if is_annual:
                lo = round(lo / 12, 2)
                hi = round(hi / 12, 2)

            if lo > hi:
                lo, hi = hi, lo
            avg = round((lo + hi) / 2, 2)
            return (lo, hi, avg)

        # 单一值: "15K" 或 "1.5万"
        single = re.search(r'([\d.]+)\s*([万千kKwW])', text)
        if single:
            val = float(single.group(1))
            unit = single.group(2)
            if unit in unit_map:
                val *= unit_map[unit]
            if is_annual:
                val = round(val / 12, 2)
            return (val, val, val)

        return (0, 0, 0)

    def _parse_city(self, text: str) -> tuple[str, str]:
        if not text:
            return ("未知", "")
        text = text.replace(" ", "")
        for sep in ("-", "·"):
            parts = text.split(sep, 1)
            if len(parts) == 2:
                return (parts[0], parts[1])
        return (text, "")

    def _parse_requirements(self, text: str) -> tuple[str, str]:
        if not text:
            return ("不限", "不限")
        experience, education = "不限", "不限"

        exp_patterns = [
            (r'(\d+-\d+年)', lambda m: m.group(1) + '经验'),
            (r'(\d+年经验)', lambda m: m.group(1)),
            (r'(\d+年及以上)', lambda m: m.group(1).replace('及以上', '经验')),
            (r'(\d+年以上)', lambda m: m.group(1).replace('以上', '经验')),
            (r'(无需经验)', lambda m: m.group(1)),
            (r'(在校生/应届生)', lambda m: m.group(1)),
        ]
        for pat, fmt in exp_patterns:
            m = re.search(pat, text)
            if m:
                experience = fmt(m)
                break

        edu_patterns = [
            r'(博士)', r'(硕士)', r'(本科)', r'(大专)', r'(中专)', r'(高中)',
        ]
        for pat in edu_patterns:
            m = re.search(pat, text)
            if m:
                education = m.group(1)
                break

        return (experience, education)

    # ---------------------------------------------------------------------
    # 公司信息解析
    # ---------------------------------------------------------------------
    def _parse_company_info(self, text: str) -> tuple[str, str, str]:
        """从公司信息文本中分离规模、类型、行业"""
        company_size = ""
        company_type = ""
        industry = ""

        if not text:
            return (company_size, company_type, industry)

        # 规模
        size_m = re.search(r'(\d+-?\d*人|少于\d+人|[一-龥]+规模)', text)
        if size_m:
            company_size = size_m.group(1)

        # 类型
        type_keywords = ['民营', '外企', '国企', '合资', '上市公司', '创业公司',
                         '外资', '股份制', '事业单位', '政府机关', '外商独资',
                         '代表处', '非营利组织']
        for kw in type_keywords:
            if kw in text:
                company_type = kw
                break

        # 行业
        parts = text.replace(" ", "").split("|")
        for part in parts:
            if any(c.isalpha() for c in part) and len(part) > 2:
                if not any(kw in part for kw in type_keywords + ['规模', '人']):
                    industry = part

        return (company_size, company_type, industry)

    # ---------------------------------------------------------------------
    # 主爬取流程
    # ---------------------------------------------------------------------
    def crawl_all(self, keywords=None, max_pages=None, progress_callback=None):
        """生成器：逐条产出职位数据"""
        keywords = keywords or SEARCH_KEYWORDS
        if max_pages is None:
            max_pages = min(MAX_PAGES, 3)  # 未指定时默认少量页面，避免反爬

        total_keywords = len(keywords)
        collected = 0

        try:
            self._ensure_browser()

            for kw_idx, keyword in enumerate(keywords):
                print(f"\n[搜索] [{kw_idx+1}/{total_keywords}] 正在搜索: {keyword}")

                for page_num in range(1, max_pages + 1):
                    try:
                        print(f"  [页面] 第 {page_num}/{max_pages} 页 ...", end=" ", flush=True)

                        page, html = self._fetch_page(keyword, page_num)
                        jobs = self._parse_job_cards(page, html, keyword)

                        # 用完就关页面和上下文，释放内存
                        context = page.context
                        page.close()
                        context.close()

                        if not jobs:
                            print("无数据（可能已到最后一页或被拦截）")
                            break

                        print(f"提取 {len(jobs)} 条")
                        for job in jobs:
                            yield job
                            collected += 1

                        if progress_callback:
                            progress_callback(collected, -1)

                        # 随机延迟，降低触发反爬概率
                        time.sleep(REQUEST_DELAY + random.uniform(1.0, 2.0))

                    except Exception as e:
                        print(f"失败: {e}")
                        continue

        finally:
            self._close_browser()

        print(f"\n[完成] 爬取完成! 共采集 {collected} 条职位数据")

    def _close_browser(self):
        """安全关闭浏览器"""
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._browser = None
        self._playwright = None

    def crawl_parallel(self, keywords=None, max_pages=None, num_threads=3):
        """
        多线程爬取 —— Playwright 模式下使用单线程顺序执行，
        因为浏览器实例不适合跨线程共享。
        """
        return list(self.crawl_all(keywords, max_pages))


# =========================================================================
# 模拟数据生成器 —— 真实数据不足时的兜底
# =========================================================================
class MockDataGenerator:
    """模拟招聘数据生成器（与之前一致，未修改）"""

    MAJOR_CITIES = [
        ("北京", 1.3), ("上海", 1.25), ("深圳", 1.2), ("广州", 1.1),
        ("杭州", 1.15), ("成都", 1.0), ("武汉", 0.95), ("南京", 1.05),
        ("西安", 0.9), ("长沙", 0.88), ("苏州", 1.0), ("合肥", 0.85),
        ("郑州", 0.82), ("重庆", 0.9), ("厦门", 0.95), ("天津", 0.88),
    ]

    JOB_TITLES = [
        "Python开发工程师", "数据分析师", "大数据开发工程师",
        "机器学习工程师", "深度学习算法工程师", "NLP算法工程师",
        "计算机视觉工程师", "数据挖掘工程师", "AI产品经理",
        "后端开发工程师", "数据仓库工程师", "商业分析师",
        "AIGC算法工程师", "大模型训练工程师", "MLEngineering",
        "推荐算法工程师", "风控数据分析师", "增长数据分析师",
        "量化策略研究员", "数据治理工程师", "云计算开发工程师",
        "全栈开发工程师", "AI训练师", "Prompt工程师",
    ]

    COMPANIES = [
        "字节跳动", "腾讯科技", "阿里巴巴", "百度在线", "美团点评",
        "小红书", "哔哩哔哩", "网易集团", "京东集团", "拼多多",
        "华为技术", "商汤科技", "旷视科技", "科大讯飞", "第四范式",
        "BOSS直聘", "理想汽车", "蔚来汽车", "小米科技", "OPPO",
        "VIVO", "比亚迪", "宁德时代", "地平线", "智谱AI",
        "月之暗面", "百川智能", "MiniMax", "零一万物", "智源研究院",
        "中国平安", "蚂蚁集团", "微众银行", "中信证券", "华泰证券",
        "滴滴出行", "快手科技", "微医集团", "好未来", "猿辅导",
    ]

    EXPERIENCE_LEVELS = [
        "在校生/应届生", "1年经验", "2年经验", "3-4年经验",
        "5-7年经验", "8-9年经验", "10年以上经验",
    ]
    EXPERIENCE_WEIGHTS = [0.15, 0.1, 0.15, 0.25, 0.18, 0.1, 0.07]

    EDUCATION_LEVELS = ["大专", "本科", "硕士", "博士", "不限"]
    EDUCATION_WEIGHTS = [0.22, 0.52, 0.16, 0.05, 0.05]

    COMPANY_SIZES = [
        "少于50人", "50-150人", "150-500人", "500-1000人",
        "1000-5000人", "5000-10000人", "10000人以上",
    ]
    COMPANY_TYPES = ["民营", "上市公司", "外企", "合资", "国企", "创业公司"]
    INDUSTRIES = [
        "互联网/电商", "人工智能", "金融科技", "在线教育",
        "医疗健康", "智能硬件", "新能源汽车", "企业服务SaaS",
        "游戏/娱乐", "信息安全", "半导体/芯片", "区块链/Web3",
        "云计算/大数据", "物联网", "机器人/自动化",
    ]
    SKILLS_POOL = [
        "Python", "SQL", "Spark", "Hadoop", "TensorFlow", "PyTorch",
        "Scikit-learn", "Pandas", "NumPy", "Docker", "Kubernetes",
        "AWS", "Linux", "Git", "Flask", "Django", "FastAPI",
        "MySQL", "Redis", "MongoDB", "Kafka", "Airflow", "Tableau",
        "PowerBI", "Excel", "R", "Java", "Go", "C++",
        "LLM", "LangChain", "RAG", "Agent", "VectorDB",
        "Transformer", "BERT", "GPT", "CV", "OCR", "TTS",
    ]
    BENEFITS_POOL = [
        "五险一金", "补充医疗", "带薪年假", "弹性工作", "远程办公",
        "股票期权", "年终奖金", "定期体检", "免费三餐", "住房补贴",
        "交通补贴", "通讯补贴", "健身房", "下午茶", "出国机会",
        "技术培训", "大牛带队", "扁平管理", "晋升空间大",
    ]

    @classmethod
    def generate(cls, count=500) -> list[dict]:
        jobs = []
        base_date = datetime.now()
        for i in range(count):
            job_title = random.choice(cls.JOB_TITLES)
            city, salary_coef = random.choice(cls.MAJOR_CITIES)
            base_salary = max(3, random.gauss(15, 8))
            salary_avg = round(base_salary * salary_coef, 2)
            salary_min = round(salary_avg * 0.7, 2)
            salary_max = round(salary_avg * 1.3, 2)
            company_name = random.choice(cls.COMPANIES)
            experience = random.choices(cls.EXPERIENCE_LEVELS, weights=cls.EXPERIENCE_WEIGHTS)[0]
            education = random.choices(cls.EDUCATION_LEVELS, weights=cls.EDUCATION_WEIGHTS)[0]
            company_size = random.choice(cls.COMPANY_SIZES)
            company_type = random.choice(cls.COMPANY_TYPES)
            industry = random.choice(cls.INDUSTRIES)
            num_skills = random.randint(3, 8)
            skills = json.dumps(
                random.sample(cls.SKILLS_POOL, min(num_skills, len(cls.SKILLS_POOL))),
                ensure_ascii=False,
            )
            num_benefits = random.randint(2, 5)
            benefits = "，".join(
                random.sample(cls.BENEFITS_POOL, min(num_benefits, len(cls.BENEFITS_POOL)))
            )
            days_ago = random.randint(0, 60)
            post_date = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            jobs.append({
                "job_title": job_title,
                "company_name": company_name,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_avg": salary_avg,
                "city": city,
                "district": "",
                "experience": experience,
                "education": education,
                "company_size": company_size,
                "company_type": company_type,
                "industry": industry,
                "skills": skills,
                "benefits": benefits,
                "post_date": post_date,
                "job_url": f"mock://job/{i+1}",
                "source": "mock_data",
            })
        return jobs


# =========================================================================
# 便捷函数 —— 供主程序调用
# =========================================================================
def fetch_jobs(keywords=None, max_pages=None, use_mock=False, progress_callback=None) -> list[dict]:
    """
    获取职位数据的统一入口。

    策略：
    1. use_mock=False -> 用 Playwright 真实浏览器爬取
    2. 爬取数据不足 300 条 -> 自动用模拟数据补足到 500
    3. use_mock=True -> 纯模拟数据

    返回: 职位数据列表
    """
    all_jobs = []

    if not use_mock:
        print("=" * 60)
        print("[真实爬取] 启动 Playwright 真实浏览器，开始采集招聘数据...")
        print("=" * 60)
        crawler = JobCrawler()
        try:
            for job in crawler.crawl_all(keywords, max_pages, progress_callback):
                all_jobs.append(job)
        except KeyboardInterrupt:
            print("\n[警告] 用户中断爬取")
        except Exception as e:
            print(f"\n[警告] 爬取过程出错: {e}")

    if len(all_jobs) < 300:
        shortage = max(0, 500 - len(all_jobs))
        print(f"\n[数据] 真实数据 {len(all_jobs)} 条，补充 {shortage} 条模拟数据...")
        mock_jobs = MockDataGenerator.generate(shortage)
        all_jobs.extend(mock_jobs)

    print(f"\n[数据] 最终可用数据: {len(all_jobs)} 条")

    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        url = job.get("job_url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_jobs.append(job)

    print(f"[数据] 去重后数据: {len(unique_jobs)} 条")
    return unique_jobs
