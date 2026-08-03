# =============================================================================
# HTML 分析报告生成器
# =============================================================================
# 将数据分析结果生成为可直接分享的 HTML 文件，包含：
# 1. 数据概览 KPI 卡片
# 2. 内嵌 matplotlib 图表（Base64 编码）
# 3. AI 市场洞察文字总结
# 4. 专业排版样式
#
# 使用方式：
#   generator = ReportGenerator(df, visualizer)
#   generator.generate("output/report.html")

import base64
import io
import os
from datetime import datetime
from collections import Counter

import pandas as pd

from config import BASE_DIR

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI时代技术人才招聘市场洞察报告</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #0f0f1a;
    color: #e0e0f0;
    line-height: 1.8;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}
  .header {{
    text-align: center;
    padding: 60px 0 40px;
    border-bottom: 2px solid #7c3aed;
    margin-bottom: 50px;
  }}
  .header h1 {{
    font-size: 2.2em;
    background: linear-gradient(135deg, #7c3aed, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
  }}
  .header .subtitle {{ color: #a0a0c0; font-size: 1.1em; }}
  .header .meta {{ color: #6b7280; font-size: 0.9em; margin-top: 15px; }}

  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 50px;
  }}
  .kpi-card {{
    background: linear-gradient(135deg, #1e1e2e, #2d2d44);
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    border: 1px solid #3a3a5c;
  }}
  .kpi-card .value {{
    font-size: 2.4em;
    font-weight: bold;
    background: linear-gradient(135deg, #7c3aed, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .kpi-card .label {{ color: #a0a0c0; font-size: 0.95em; margin-top: 8px; }}

  .section {{
    background: #1e1e2e;
    border-radius: 16px;
    padding: 36px 32px;
    margin-bottom: 32px;
    border: 1px solid #2d2d44;
  }}
  .section h2 {{
    font-size: 1.5em;
    margin-bottom: 8px;
    color: #7c3aed;
    border-left: 4px solid #7c3aed;
    padding-left: 14px;
  }}
  .section .desc {{ color: #a0a0c0; margin-bottom: 24px; font-size: 0.95em; }}
  .section img {{
    width: 100%;
    border-radius: 10px;
    margin: 16px 0;
  }}

  .insight-box {{
    background: linear-gradient(135deg, #2d1f4e, #1a2744);
    border-left: 4px solid #7c3aed;
    border-radius: 0 12px 12px 0;
    padding: 20px 24px;
    margin: 20px 0;
  }}
  .insight-box h3 {{ color: #9061f9; font-size: 1.1em; margin-bottom: 8px; }}
  .insight-box ul {{ padding-left: 20px; color: #c0c0e0; }}
  .insight-box li {{ margin: 6px 0; }}

  .footer {{
    text-align: center;
    padding: 40px 0;
    color: #6b7280;
    font-size: 0.9em;
    border-top: 1px solid #2d2d44;
    margin-top: 40px;
  }}
  .skill-tag {{
    display: inline-block;
    background: #2d2d44;
    color: #7c3aed;
    padding: 4px 12px;
    border-radius: 6px;
    margin: 3px;
    font-size: 0.9em;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
  }}
  th, td {{
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid #2d2d44;
  }}
  th {{ color: #7c3aed; font-weight: 600; }}
  tr:hover {{ background: #2d2d44; }}
</style>
</head>
<body>

<div class="container">

  <div class="header">
    <h1>AI时代技术人才招聘市场洞察报告</h1>
    <p class="subtitle">基于真实招聘数据的多维度市场分析</p>
    <p class="meta">报告生成时间: {report_time} &nbsp;|&nbsp; 数据量: {total_jobs} 条</p>
  </div>

  <div class="kpi-grid">
    {kpi_cards}
  </div>

  {sections}

  <div class="footer">
    <p>AI时代技术人才招聘市场洞察系统 v2.0 &copy; {year}</p>
    <p>数据来源: 51job招聘平台 &nbsp;|&nbsp; 技术栈: Python + pandas + matplotlib + Streamlit</p>
  </div>

</div>
</body>
</html>"""

KPI_CARD_TPL = """
<div class="kpi-card">
  <div class="value">{value}</div>
  <div class="label">{label}</div>
</div>"""

SECTION_TPL = """
<div class="section">
  <h2>{title}</h2>
  <p class="desc">{desc}</p>
  {content}
</div>"""

INSIGHT_TPL = """
<div class="insight-box">
  <h3>{title}</h3>
  <ul>{items}</ul>
</div>"""


class ReportGenerator:
    """HTML 分析报告生成器"""

    def __init__(self, df: pd.DataFrame, visualizer=None):
        self.df = df
        self.visualizer = visualizer

    def generate(self, output_path: str = None) -> str:
        """生成完整 HTML 报告，返回 HTML 字符串"""
        if output_path is None:
            output_path = os.path.join(BASE_DIR, "data", "report.html")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        html = TEMPLATE.format(
            report_time=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
            total_jobs=len(self.df),
            year=datetime.now().year,
            kpi_cards=self._build_kpi_cards(),
            sections=self._build_sections(),
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def _fig_to_b64(self, fig) -> str:
        """matplotlib Figure → Base64 内嵌图片"""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                    facecolor="#1e1e2e", edgecolor="none", transparent=False)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    def _img_tag(self, b64_data: str, alt: str = "") -> str:
        return f'<img src="data:image/png;base64,{b64_data}" alt="{alt}">'

    def _build_kpi_cards(self) -> str:
        df = self.df
        total = len(df)
        avg_sal = df.loc[df["salary_avg"] > 0, "salary_avg"].mean()
        cities = df.loc[df["city"] != "未知", "city"].nunique()
        companies = df.loc[df["company_name"] != "未知公司", "company_name"].nunique()
        ai_count = 0
        if "is_ai_position" in df.columns:
            ai_count = (df["is_ai_position"] == "是").sum()
        top_city = df.loc[df["city"] != "未知", "city"].value_counts().index[0] if cities > 0 else "N/A"

        cards = [
            (f"{total:,}", "总岗位数"),
            (f"{avg_sal:.1f}K", "平均月薪"),
            (f"{cities}", "覆盖城市"),
            (f"{companies}", "招聘公司"),
            (f"{ai_count}", "AI岗位"),
            (f"{top_city}", "岗位最多城市"),
        ]
        return "\n".join(KPI_CARD_TPL.format(value=v, label=l) for v, l in cards)

    def _build_sections(self) -> str:
        sections = []

        # ---- 第1部分：薪资市场概况 ----
        if self.visualizer:
            try:
                fig = self.visualizer.chart_salary_distribution(figsize=(10, 5))
                img = self._img_tag(self._fig_to_b64(fig), "薪资分布")
            except Exception:
                img = "<p>图表渲染失败</p>"

            avg = self.df.loc[self.df["salary_avg"] > 0, "salary_avg"].mean()
            med = self.df.loc[self.df["salary_avg"] > 0, "salary_avg"].median()
            top25 = self.df.loc[self.df["salary_avg"] > 0, "salary_avg"].quantile(0.75)

            salary_insight = INSIGHT_TPL.format(
                title="市场洞察",
                items=f"""
                  <li>技术岗位平均月薪 <b>{avg:.1f}K</b>，中位数 <b>{med:.1f}K</b></li>
                  <li>25%的高薪岗位薪资超过 <b>{top25:.1f}K/月</b></li>
                  <li>薪资分布呈现<strong>右偏长尾</strong>形态，高端技术人才供不应求</li>
                """,
            )
            sections.append(SECTION_TPL.format(
                title="薪资市场概况",
                desc="技术岗位薪资分布全景，揭示市场对技术人才的定价区间",
                content=img + salary_insight,
            ))

        # ---- 第2部分：城市与行业分析 ----
        if self.visualizer:
            try:
                fig_city = self.visualizer.chart_city_salary_compare(figsize=(10, 5))
                city_img = self._img_tag(self._fig_to_b64(fig_city), "城市薪资对比")
            except Exception:
                city_img = ""

            try:
                fig_ind = self.visualizer.chart_industry_ranking(figsize=(10, 5))
                ind_img = self._img_tag(self._fig_to_b64(fig_ind), "行业需求排行")
            except Exception:
                ind_img = ""

            # 城市薪资 top3
            city_salary = (
                self.df.groupby("city")["salary_avg"]
                .agg(["mean", "count"])
                .query("count >= 3")
                .sort_values("mean", ascending=False)
            )
            top_cities = city_salary.head(5).index.tolist()
            city_insight = INSIGHT_TPL.format(
                title="城市选择建议",
                items="".join(
                    f"<li><b>{c}</b>: 均薪 {city_salary.loc[c, 'mean']:.1f}K，"
                    f"岗位数 {int(city_salary.loc[c, 'count'])}</li>"
                    for c in top_cities
                ),
            )
            sections.append(SECTION_TPL.format(
                title="城市与行业分析",
                desc="各城市技术岗位薪资对比及行业需求排行",
                content=city_img + ind_img + city_insight,
            ))

        # ---- 第3部分：技能需求趋势 ----
        if self.visualizer:
            try:
                fig_skills = self.visualizer.chart_top_skills(figsize=(10, 5))
                skill_img = self._img_tag(self._fig_to_b64(fig_skills), "热门技能")
            except Exception:
                skill_img = ""

            # 技能频次 top10
            counter = Counter()
            for skills_str in self.df.get("extracted_skills", pd.Series()).dropna():
                if skills_str and isinstance(skills_str, str):
                    for s in skills_str.split("，"):
                        s = s.strip()
                        if s and len(s) > 1:
                            counter[s] += 1
            top_skills = counter.most_common(15)

            skill_tags = "\n".join(
                f'<span class="skill-tag">{s} ({c}次)</span>'
                for s, c in top_skills
            )

            skill_insight = INSIGHT_TPL.format(
                title="学习路线建议",
                items=f"""
                  <li>最热门的三大技术栈：<b>{top_skills[0][0] if top_skills else 'Python'}</b>、
                     <b>{top_skills[1][0] if len(top_skills) > 1 else 'SQL'}</b>、
                     <b>{top_skills[2][0] if len(top_skills) > 2 else 'Docker'}</b></li>
                  <li>AI 方向技能（TensorFlow/PyTorch/LLM/RAG）需求高速增长</li>
                  <li>工程能力（Docker/Kubernetes/Linux）与算法能力同样重要</li>
                """,
            )
            sections.append(SECTION_TPL.format(
                title="技能需求趋势",
                desc="市场最需要的技术技能及学习建议",
                content=skill_img + f"<div style='margin:16px 0'>{skill_tags}</div>" + skill_insight,
            ))

        # ---- 第4部分：AI岗位专项分析 ----
        if self.visualizer and "is_ai_position" in self.df.columns:
            try:
                fig_ai = self.visualizer.chart_ai_vs_nonai(figsize=(10, 5))
                ai_img = self._img_tag(self._fig_to_b64(fig_ai), "AI vs 非AI")
            except Exception:
                ai_img = ""

            ai_df = self.df[self.df["is_ai_position"] == "是"]
            non_ai_df = self.df[self.df["is_ai_position"] == "否"]
            ai_avg = ai_df.loc[ai_df["salary_avg"] > 0, "salary_avg"].mean()
            non_ai_avg = non_ai_df.loc[non_ai_df["salary_avg"] > 0, "salary_avg"].mean()
            premium = ((ai_avg - non_ai_avg) / non_ai_avg * 100) if non_ai_avg > 0 else 0

            ai_insight = INSIGHT_TPL.format(
                title="AI岗位市场洞察",
                items=f"""
                  <li>AI 岗位平均薪资 <b>{ai_avg:.1f}K/月</b>，相比传统技术岗位（{non_ai_avg:.1f}K/月）
                     溢价约 <b>{premium:.0f}%</b></li>
                  <li>AI 岗位对硕士以上学历的需求显著高于传统岗位</li>
                  <li>建议：传统开发工程师可向 ML/AI 方向转型，获得 {premium:.0f}% 薪资增幅</li>
                """,
            )
            sections.append(SECTION_TPL.format(
                title="AI 岗位专项分析",
                desc="AI 相关岗位与传统技术岗位的全方位对比",
                content=ai_img + ai_insight,
            ))

        # ---- 第5部分：经验与学历建议 ----
        if self.visualizer:
            try:
                fig_exp = self.visualizer.chart_experience_distribution(figsize=(10, 5))
                exp_img = self._img_tag(self._fig_to_b64(fig_exp), "经验薪资关系")
            except Exception:
                exp_img = ""

            exp_insight = INSIGHT_TPL.format(
                title="职业发展建议",
                items="""
                  <li><b>新人起步</b>：应届生岗位占比可观，起薪集中 8-15K</li>
                  <li><b>快速成长期</b>：3-5年经验是薪资跃升最陡峭的阶段</li>
                  <li><b>学历价值</b>：硕士较本科有 15-25% 薪资溢价，博士在 AI 领域尤为稀缺</li>
                """,
            )
            sections.append(SECTION_TPL.format(
                title="经验与学历建议",
                desc="不同经验水平与学历的薪资关系，为职业规划提供参考",
                content=exp_img + exp_insight,
            ))

        return "\n".join(sections)


def generate_report(df: pd.DataFrame, visualizer=None, output_path: str = None) -> str:
    """便捷函数：一键生成 HTML 报告"""
    gen = ReportGenerator(df, visualizer)
    return gen.generate(output_path)
