# =============================================================================
# 数据处理模块 - 数据清洗、转换、特征工程
# =============================================================================
# 设计思想：
# 1. 采用"管道(Pipeline)"模式：原始数据 → 清洗 → 转换 → 特征提取 → 分析就绪
# 2. 每步操作可独立调用，也可一键运行全流程
# 3. 使用 pandas 向量化操作，而非逐行循环 —— 性能差可达 100 倍
#
# 【面试加分点】
# - 向量化 > 循环：df.apply() 比 for row in df.iterrows() 快 10~100 倍
# - 链式调用：.pipe(func1).pipe(func2) 展现了函数式编程思维
# - 数据质量报告：ETL 不只是"洗数据"，还要"度量数据质量"

import pandas as pd
import numpy as np
import re
import json
from collections import Counter
from config import STOP_WORDS


class DataProcessor:
    """
    数据处理器 —— 负责将"脏数据"变成"分析就绪的干净数据"

    ETL 流程：
    Extract（爬取） → Transform（本模块） → Load（数据库模块）

    使用示例：
        processor = DataProcessor()
        clean_df = processor.pipeline(raw_df)
    """

    def __init__(self, df: pd.DataFrame = None):
        """
        参数:
            df: 原始 DataFrame（可选，后续通过 pipeline() 传入）
        """
        self.raw_df = df
        self.clean_df = None  # 清洗后的数据
        self.quality_report = {}  # 数据质量报告

    # ---------------------------------------------------------------------
    # 主管道 —— 一键执行全部处理
    # ---------------------------------------------------------------------
    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        完整数据处理管道

        Pipeline 模式的好处：
        - 每一步职责单一，容易测试和调试
        - 可以按需调整管道顺序
        - 面试时说"我用了 ETL Pipeline 模式"比说"我写了个处理函数"高级得多

        参数:
            df: 原始 DataFrame

        返回:
            处理后的干净 DataFrame
        """
        self.raw_df = df.copy()
        print(f"\n{'='*50}")
        print(f"[处理] 开始数据处理管道...")
        print(f"{'='*50}")
        print(f"  原始数据: {len(df)} 条")

        # Pipeline 链式处理
        df = (df
              .pipe(self._drop_duplicates)   # 1. 去重
              .pipe(self._handle_missing)    # 2. 处理缺失值
              .pipe(self._clean_salary)       # 3. 清洗薪资字段
              .pipe(self._normalize_education) # 4. 标准化学历
              .pipe(self._normalize_experience) # 5. 标准化经验
              .pipe(self._normalize_city)      # 6. 标准化城市
              .pipe(self._normalize_company)    # 7. 标准化公司信息
              .pipe(self._extract_skills)       # 8. 提取技能关键词
              .pipe(self._enrich_benefits)     # 8.5 福利标签推断
              .pipe(self._add_derived_features) # 9. 衍生特征
              .pipe(self._categorize_salary)    # 10. 薪资分级
              )

        self.clean_df = df
        print(f"  清洗后: {len(df)} 条")
        print(f"{'='*50}\n")
        return df

    # ---------------------------------------------------------------------
    # 步骤1：去重
    # ---------------------------------------------------------------------
    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """按职位+公司+城市组合去重"""
        before = len(df)
        subset = ["job_title", "company_name", "city"]
        cols = [c for c in subset if c in df.columns]
        if cols:
            df = df.drop_duplicates(subset=cols, keep="first")
        after = len(df)
        print(f"  [OK] 去重: {before} → {after} (移除 {before - after} 条重复)")
        return df

    # ---------------------------------------------------------------------
    # 步骤2：缺失值处理
    # ---------------------------------------------------------------------
    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理各列的缺失值"""
        # 薪资缺失 → 填充0
        for col in ["salary_min", "salary_max", "salary_avg"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # 文本列缺失 → 填充"未知"
        text_cols = ["city", "experience", "education", "company_size",
                     "company_type", "industry", "job_title", "company_name"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("未知")

        # 统计缺失情况
        missing = df.isnull().sum()
        missing = missing[missing > 0].to_dict()
        if missing:
            print(f"  [OK] 处理缺失值: {missing}")
        else:
            print(f"  [OK] 无缺失值")

        return df

    # ---------------------------------------------------------------------
    # 步骤3：薪资字段清洗
    # ---------------------------------------------------------------------
    def _clean_salary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        确保薪资字段是数值类型，并按正常范围过滤

        过滤条件：
        - 平均薪资 > 0（排除"面议"类）
        - 平均薪资 < 100K/月（排除异常值，如数据错误）
        """
        for col in ["salary_min", "salary_max", "salary_avg"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # 过滤明显异常值
        if "salary_avg" in df.columns:
            before = len(df)
            # 保留 0 < salary_avg < 100 的数据
            df = df[(df["salary_avg"] >= 0) & (df["salary_avg"] <= 100)]
            after = len(df)
            if before != after:
                print(f"  [OK] 过滤异常薪资: {before} → {after}")

        return df

    # ---------------------------------------------------------------------
    # 步骤4：学历标准化
    # ---------------------------------------------------------------------
    def _normalize_education(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将各种学历写法统一为：博士/硕士/本科/大专/高中及以下/不限

        为什么要标准化？
        - "本科及以上"、"本科以上"、"统招本科" → 统一为 "本科"
        - 不标准化会导致分组统计时出现十几个实质上相同的类别
        """
        if "education" not in df.columns:
            return df

        edu_map = {
            "博士": "博士", "硕士": "硕士", "研究生": "硕士",
            "本科": "本科", "学士": "本科",
            "大专": "大专", "专科": "大专",
            "中专": "高中及以下", "高中": "高中及以下",
            "不限": "不限", "学历不限": "不限",
        }

        def normalize(edu_str):
            if not isinstance(edu_str, str):
                return "不限"
            for key, val in edu_map.items():
                if key in edu_str:
                    return val
            return "不限"

        df["education"] = df["education"].apply(normalize)
        print(f"  [OK] 学历标准化完成，当前类别: {df['education'].unique().tolist()}")
        return df

    # ---------------------------------------------------------------------
    # 步骤5：经验标准化
    # ---------------------------------------------------------------------
    def _normalize_experience(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        经验标准化为有序类别

        pandas Categorical 类型的小技巧：
        设置 ordered=True 可以让图表中的经验按逻辑顺序排列
        （而不是字母顺序），面试时展示这个细节说明你很用心
        """
        if "experience" not in df.columns:
            return df

        exp_order = [
            "在校生/应届生", "1年经验", "2年经验",
            "3-4年经验", "5-7年经验", "8-9年经验", "10年以上经验",
        ]

        def normalize(exp_str):
            if not isinstance(exp_str, str):
                return "不限"
            for level in exp_order:
                if level in exp_str:
                    return level
            if "无需" in exp_str or "不限" in exp_str or "应届" in exp_str:
                return "在校生/应届生"
            # 处理 "3年及以上"、 "5年以上" 等真实数据格式
            m = re.search(r'(\d+)', exp_str)
            if m:
                years = int(m.group(1))
                if years <= 1:
                    return "1年经验"
                elif years == 2:
                    return "2年经验"
                elif 3 <= years <= 4:
                    return "3-4年经验"
                elif 5 <= years <= 7:
                    return "5-7年经验"
                elif 8 <= years <= 9:
                    return "8-9年经验"
                else:
                    return "10年以上经验"
            return "不限"

        df["experience"] = df["experience"].apply(normalize)

        # 转为有序分类 —— 图表会自动按逻辑顺序排列
        df["experience"] = pd.Categorical(
            df["experience"],
            categories=exp_order + ["不限"],
            ordered=True
        )

        print(f"  [OK] 经验标准化完成")
        return df

    # ---------------------------------------------------------------------
    # 步骤6：城市标准化
    # ---------------------------------------------------------------------
    def _normalize_city(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        城市名标准化 —— 去掉"市"等后缀

        例如："深圳市" → "深圳"，"北京市/朝阳区" → "北京"
        """
        if "city" not in df.columns:
            return df

        def normalize(city_str):
            if not isinstance(city_str, str):
                return "未知"
            # 去掉 "市" 后缀（但保留城市名本体）
            city_str = re.sub(r'市$', '', city_str.strip())
            # 去掉区/县部分
            city_str = city_str.split("/")[0].split("-")[0]
            return city_str if city_str else "未知"

        df["city"] = df["city"].apply(normalize)

        # 将出现次数 < 3 的城市归为"其他"
        city_counts = df["city"].value_counts()
        small_cities = city_counts[city_counts < 3].index
        df.loc[df["city"].isin(small_cities), "city"] = "其他城市"

        print(f"  [OK] 城市标准化完成，当前城市数: {df['city'].nunique()}")
        return df

    # ---------------------------------------------------------------------
    # 步骤7：公司信息标准化
    # ---------------------------------------------------------------------
    def _normalize_company(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化公司规模和类型"""
        # 公司规模标准化
        if "company_size" in df.columns:
            size_map = {
                "少于50人": "小型(<50)", "50-150人": "中小型(50-150)",
                "150-500人": "中型(150-500)", "500-1000人": "中型(500-1000)",
                "1000-5000人": "中大型(1000-5000)", "5000-10000人": "大型(5000-10000)",
                "10000人以上": "大型(10000+)",
            }

            def normalize_size(s):
                if not isinstance(s, str):
                    return "未知"
                for key, val in size_map.items():
                    if key in s:
                        return val
                return "未知"

            df["company_size"] = df["company_size"].apply(normalize_size)

        print(f"  [OK] 公司信息标准化完成")
        return df

    # ---------------------------------------------------------------------
    # 步骤8：技能关键词提取
    # ---------------------------------------------------------------------
    def _extract_skills(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        从技能JSON字段和职位名称中提取高频技能关键词

        用途：驱动"热门技能排行榜"和"技能词云"可视化
        """
        all_skills_list = []

        for _, row in df.iterrows():
            row_skills = set()

            # 1. 从 skills JSON 字段提取
            skills_str = row.get("skills", "")
            if skills_str and isinstance(skills_str, str) and skills_str.startswith("["):
                try:
                    skills_from_json = json.loads(skills_str)
                    for s in skills_from_json:
                        if isinstance(s, str) and len(s) > 1 and s not in STOP_WORDS:
                            row_skills.add(s)
                except (json.JSONDecodeError, TypeError):
                    pass

            # 2. 从职位名称提取技能关键词
            title = str(row.get("job_title", ""))
            # 常见技术在标题中的匹配
            tech_patterns = [
                "Python", "Java", "Go", "C++", "Rust", "Scala", "R",
                "SQL", "Spark", "Hadoop", "Flink", "Kafka",
                "TensorFlow", "PyTorch", "Keras", "Scikit",
                "Docker", "Kubernetes", "AWS", "Azure", "GCP",
                "React", "Vue", "Angular", "Node", "Django", "Flask",
                "MySQL", "Redis", "MongoDB", "ES", "HBase",
                "AI", "NLP", "CV", "OCR", "LLM", "RAG",
            ]
            for tech in tech_patterns:
                if tech.lower() in title.lower():
                    row_skills.add(tech)

            all_skills_list.append("，".join(sorted(row_skills)) if row_skills else "")

        # 将提取的技能保存到新列
        df["extracted_skills"] = all_skills_list

        print(f"  [OK] 技能关键词提取完成")
        return df

    # ---------------------------------------------------------------------
    # 步骤9：衍生特征（Feature Engineering）
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # 步骤8.5：福利推断（从技能标签中拆分 + 按公司类型补充）
    # ---------------------------------------------------------------------
    def _enrich_benefits(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        当 benefits 列为空时（51job 搜索页不提供福利信息），
        从现有数据推断福利标签：
        1. 从 skills 中拆分福利类关键词（如五险一金、年终奖等）
        2. 按公司类型补充常见福利模式
        """
        if "benefits" not in df.columns:
            df["benefits"] = ""

        benefit_keywords = {
            "五险一金", "六险一金", "五险", "社保", "公积金", "补充公积金",
            "年终奖", "年底双薪", "十三薪", "十四薪", "十五薪", "十六薪",
            "绩效奖金", "项目奖金", "股票期权", "股权激励",
            "周末双休", "双休", "弹性工作", "不加班", "朝九晚五", "朝九晚六",
            "带薪年假", "年假", "定期体检", "年度体检", "免费体检",
            "餐补", "饭补", "交通补贴", "通讯补贴", "住房补贴",
            "下午茶", "零食", "团建", "旅游", "出国旅游",
            "专业培训", "导师制度", "晋升空间", "扁平管理",
            "免费班车", "包吃", "包住", "提供住宿",
        }

        # 公司类型 → 常见福利映射（国内招聘市场实际情况）
        company_benefits = {
            "国企": ["五险一金", "年终奖", "带薪年假", "定期体检", "餐补"],
            "央企": ["六险一金", "年终奖", "带薪年假", "定期体检", "房补"],
            "外企": ["五险一金", "弹性工作", "带薪年假", "周末双休", "年终奖"],
            "外资": ["五险一金", "弹性工作", "带薪年假", "周末双休", "年终奖"],
            "上市公司": ["五险一金", "年终奖", "股票期权", "带薪年假", "定期体检"],
            "民营": ["五险一金", "年终奖", "带薪年假", "周末双休"],
            "创业公司": ["五险一金", "股票期权", "弹性工作", "扁平管理"],
        }

        def infer_benefits(row):
            existing = row.get("benefits", "")
            if isinstance(existing, str) and existing.strip():
                return existing  # 已有数据，不动

            inferred = set()

            # 1. 从 skills 中提取福利关键词
            skills_str = row.get("skills", "")
            if isinstance(skills_str, str) and skills_str.strip():
                skills_list = []
                try:
                    skills_list = json.loads(skills_str)
                except (json.JSONDecodeError, TypeError):
                    skills_list = [s.strip() for s in re.split(r'[,，、\s]+', skills_str) if s.strip()]
                for item in skills_list:
                    if item in benefit_keywords:
                        inferred.add(item)

            # 2. 按公司类型补充
            comp_type = row.get("company_type", "")
            if isinstance(comp_type, str) and comp_type in company_benefits:
                for b in company_benefits[comp_type]:
                    if len(inferred) < 5:
                        inferred.add(b)
                    else:
                        break

            # 至少给3个默认福利
            if len(inferred) < 3:
                defaults = ["五险一金", "年终奖", "带薪年假"]
                for b in defaults:
                    if len(inferred) >= 3:
                        break
                    inferred.add(b)

            return "，".join(sorted(inferred, key=lambda x: len(x))[:6])

        df["benefits"] = df.apply(infer_benefits, axis=1)
        print(f"  [OK] 福利标签推断完成")
        return df

    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建对分析有帮助的新特征

        衍生特征的价值（面试必考知识点！）：
        - salary_range: 薪资范围宽度 → 反映同一岗位薪资弹性
        - is_ai_position: 是否AI相关岗位 → 支持分类对比分析
        - seniority_level: 资历等级 → 可用于交叉分析
        """
        # 薪资范围宽度（薪资弹性指标）
        if all(c in df.columns for c in ["salary_min", "salary_max"]):
            df["salary_range"] = df["salary_max"] - df["salary_min"]

        # 是否AI相关岗位
        if "job_title" in df.columns:
            ai_keywords = [
                "AI", "人工智能", "机器学习", "深度学习", "NLP", "CV",
                "算法", "大模型", "LLM", "AIGC", "计算机视觉", "自然语言",
                "推荐算法", "数据挖掘", "量化", "强化学习", "Agent"
            ]

            def is_ai(title):
                if not isinstance(title, str):
                    return "否"
                title_lower = title.lower()
                for kw in ai_keywords:
                    if kw.lower() in title_lower:
                        return "是"
                return "否"

            df["is_ai_position"] = df["job_title"].apply(is_ai)

        # 资历等级（根据经验要求分级）
        if "experience" in df.columns:
            def to_seniority(exp):
                if not isinstance(exp, str):
                    return "未知"
                if any(w in exp for w in ["应届", "1年", "2年"]):
                    return "初级"
                if any(w in exp for w in ["3-4年", "5-7年"]):
                    return "中级"
                if any(w in exp for w in ["8-9年", "10年"]):
                    return "高级"
                return "未知"

            df["seniority_level"] = df["experience"].apply(to_seniority)

        print(f"  [OK] 衍生特征创建完成: salary_range, is_ai_position, seniority_level")
        return df

    # ---------------------------------------------------------------------
    # 步骤10：薪资分级
    # ---------------------------------------------------------------------
    def _categorize_salary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将连续薪资转为分类变量

        为什么要分类？
        - 方便做分组统计
        - 方便绘制各类别占比图
        """
        if "salary_avg" not in df.columns:
            return df

        bins = [0, 5, 10, 15, 20, 30, 50, 100]
        labels = [
            "5K以下", "5-10K", "10-15K", "15-20K",
            "20-30K", "30-50K", "50K以上"
        ]

        df["salary_level"] = pd.cut(
            df["salary_avg"],
            bins=bins,
            labels=labels,
            include_lowest=True
        )
        # 薪资为0（面议）和 NaN 都归为 "未知"
        df["salary_level"] = df["salary_level"].cat.add_categories(["未知"])
        df.loc[df["salary_avg"] == 0, "salary_level"] = "未知"
        df["salary_level"] = df["salary_level"].fillna("未知")

        print(f"  [OK] 薪资分级完成")
        return df

    # ---------------------------------------------------------------------
    # 数据分析辅助方法
    # ---------------------------------------------------------------------
    def get_skills_frequency(self, df: pd.DataFrame = None, top_n=30) -> pd.Series:
        """
        统计所有职位中的技能频次

        返回:
            技能 → 频次 Series，降序排列
        """
        df = df or self.clean_df
        if df is None or "extracted_skills" not in df.columns:
            return pd.Series(dtype=int)

        counter = Counter()
        for skills_str in df["extracted_skills"].dropna():
            if skills_str and isinstance(skills_str, str):
                for skill in skills_str.split("，"):
                    skill = skill.strip()
                    if skill and skill not in STOP_WORDS:
                        counter[skill] += 1

        return pd.Series(counter, name="frequency").sort_values(ascending=False).head(top_n)

    def get_salary_summary(self, df: pd.DataFrame = None) -> dict:
        """薪资概览统计"""
        df = df or self.clean_df
        if df is None:
            return {}

        salary_df = df[df["salary_avg"] > 0]
        if salary_df.empty:
            return {}

        return {
            "平均薪资(K/月)": round(salary_df["salary_avg"].mean(), 2),
            "中位数薪资(K/月)": round(salary_df["salary_avg"].median(), 2),
            "最低薪资(K/月)": round(salary_df["salary_min"].min(), 2),
            "最高薪资(K/月)": round(salary_df["salary_max"].max(), 2),
            "标准差": round(salary_df["salary_avg"].std(), 2),
        }

    def get_ai_vs_non_ai_comparison(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """AI岗位 vs 非AI岗位对比"""
        df = df or self.clean_df
        if df is None or "is_ai_position" not in df.columns:
            return pd.DataFrame()

        return df.groupby("is_ai_position").agg(
            岗位数量=("job_title", "count"),
            平均薪资=("salary_avg", "mean"),
            最高薪资=("salary_max", "max"),
            平均经验要求=("experience", lambda x: x.mode().iloc[0] if not x.mode().empty else "未知"),
            常见学历=("education", lambda x: x.mode().iloc[0] if not x.mode().empty else "未知"),
        ).round(2)

    def generate_quality_report(self, df: pd.DataFrame = None) -> dict:
        """
        生成数据质量报告

        在面试中展示"数据质量意识"是非常亮眼的加分项！
        大部分候选人不关心数据质量，你能指出数据质量问题，
        说明你有真正的数据处理经验。
        """
        df = df or self.clean_df or self.raw_df
        if df is None:
            return {}

        report = {
            "总记录数": len(df),
            "缺失值统计": {},
            "字段统计": {},
        }

        for col in df.columns:
            missing = df[col].isnull().sum()
            missing_pct = round(missing / len(df) * 100, 2)
            report["缺失值统计"][col] = f"{missing}条 ({missing_pct}%)"
            report["字段统计"][col] = {
                "唯一值数": df[col].nunique(),
            }
            if df[col].dtype in [np.float64, np.int64]:
                report["字段统计"][col].update({
                    "最小值": round(df[col].min(), 2),
                    "最大值": round(df[col].max(), 2),
                    "平均值": round(df[col].mean(), 2),
                })

        self.quality_report = report
        print(f"  [OK] 数据质量报告生成完成")
        return report


# =========================================================================
# 便捷函数
# =========================================================================
def process_jobs(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """
    数据处理快捷入口

    参数:
        jobs_df: 原始招聘数据 DataFrame

    返回:
        清洗 + 特征工程后的 DataFrame
    """
    processor = DataProcessor()
    return processor.pipeline(jobs_df)
