# =============================================================================
# AI人才市场洞察系统 - Streamlit Web 应用
# =============================================================================
# 启动方式: streamlit run web_app.py
# 或通过 main.py: python main.py --web
#
# 与 tkinter 桌面版相比，Web 版优势：
# - 可通过浏览器访问，支持移动端
# - 使用 plotly 实现交互式图表（悬停/缩放/筛选）
# - 可部署到 Streamlit Cloud
# - 实时筛选和交叉分析

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import json

from config import COLORS, FONT_FAMILY
from modules.database import Database
from modules.data_processor import DataProcessor
from modules.crawler import MockDataGenerator, fetch_jobs
from modules.report_generator import ReportGenerator

# ---- 页面配置 ----
st.set_page_config(
    page_title="AI人才招聘市场洞察系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义 CSS
st.markdown("""
<style>
  .main .block-container { padding-top: 2rem; }
  .stMetric { background: linear-gradient(135deg, #1e1e2e, #2d2d44); border-radius: 12px; padding: 16px; border: 1px solid #3a3a5c; }
  .stMetric label { color: #a0a0c0 !important; }
  .stMetric [data-testid="stMetricValue"] { color: #7c3aed !important; font-size: 2rem !important; }
  section[data-testid="stSidebar"] { background: #1e1e2e; }
</style>
""", unsafe_allow_html=True)


# ---- 数据加载（缓存） ----
@st.cache_resource
def load_data(use_mock: bool = True):
    """加载并处理数据，使用 Streamlit 缓存避免重复加载"""
    db = Database()
    count = db.get_count()

    if count < 100 or use_mock:
        # 生成演示数据
        jobs = MockDataGenerator.generate(500)
        db.clear_all()
        db.insert_jobs(jobs)

    df = db.to_dataframe()
    df = DataProcessor().pipeline(df)
    return df, db


# ---- 初始化 ----
if "df" not in st.session_state:
    with st.spinner("正在加载数据..."):
        df, db = load_data(use_mock=True)
        st.session_state.df = df
        st.session_state.db = db

df = st.session_state.df

# ---- 侧边栏筛选器 ----
st.sidebar.title("AI人才市场洞察系统")
st.sidebar.markdown("---")

# 城市筛选
cities = sorted(df[df["city"] != "未知"]["city"].unique().tolist())
selected_cities = st.sidebar.multiselect("城市", cities, default=[])

# 学历筛选
edu_options = sorted(df["education"].unique().tolist())
selected_edu = st.sidebar.multiselect("学历要求", edu_options, default=[])

# 薪资区间
salary_min_val = float(df[df["salary_avg"] > 0]["salary_avg"].quantile(0.05))
salary_max_val = float(df[df["salary_avg"] > 0]["salary_avg"].quantile(0.95))
salary_range = st.sidebar.slider(
    "薪资区间 (K/月)", min_value=0, max_value=100, value=(0, 100)
)

# AI 岗位筛选
ai_filter = "全部"
if "is_ai_position" in df.columns:
    ai_filter = st.sidebar.radio("岗位类型", ["全部", "AI岗位", "非AI岗位"], horizontal=True)

# 经验筛选
exp_options = sorted(df["experience"].dropna().unique().tolist())
selected_exp = st.sidebar.multiselect("经验要求", exp_options, default=[])

st.sidebar.markdown("---")
st.sidebar.caption(f"数据量: {len(df)} 条 | 覆盖 {df['city'].nunique()} 城市")

# ---- 应用筛选 ----
filtered_df = df.copy()
if selected_cities:
    filtered_df = filtered_df[filtered_df["city"].isin(selected_cities)]
if selected_edu:
    filtered_df = filtered_df[filtered_df["education"].isin(selected_edu)]
if selected_exp:
    filtered_df = filtered_df[filtered_df["experience"].isin(selected_exp)]
filtered_df = filtered_df[
    (filtered_df["salary_avg"] >= salary_range[0]) & (filtered_df["salary_avg"] <= salary_range[1])
]
if "is_ai_position" in df.columns and ai_filter != "全部":
    filtered_df = filtered_df[filtered_df["is_ai_position"] == ("是" if ai_filter == "AI岗位" else "否")]


# ---- 顶部 KPI 指标 ----
kpi_total = len(filtered_df)
kpi_avg_sal = round(filtered_df[filtered_df["salary_avg"] > 0]["salary_avg"].mean(), 1)
kpi_cities = filtered_df[filtered_df["city"] != "未知"]["city"].nunique()
kpi_ai = (filtered_df["is_ai_position"] == "是").sum() if "is_ai_position" in filtered_df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("总岗位", f"{kpi_total:,}", delta=None)
col2.metric("平均月薪", f"{kpi_avg_sal}K", delta=None)
col3.metric("覆盖城市", str(kpi_cities), delta=None)
col4.metric("AI 岗位", str(kpi_ai), delta=None)


# ---- Tab 分页 ----
tab1, tab2, tab3, tab4 = st.tabs(["概览仪表盘", "薪资分析", "技能与行业", "AI 专项对比"])

# =========================================================================
# Tab 1: 概览仪表盘
# =========================================================================
with tab1:
    st.subheader("人才市场全景洞察")

    col_a, col_b = st.columns(2)

    with col_a:
        # 城市岗位分布
        city_counts = filtered_df["city"].value_counts().head(10)
        fig = px.bar(
            x=city_counts.values, y=city_counts.index,
            orientation="h", color=city_counts.values,
            color_continuous_scale=px.colors.sequential.Plasma,
            title="城市岗位分布 Top10",
            labels={"x": "岗位数", "y": ""},
        )
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="#e0e0f0")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # 学历分布
        edu_counts = filtered_df["education"].value_counts()
        fig = px.pie(
            values=edu_counts.values, names=edu_counts.index,
            title="学历要求分布",
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", font_color="#e0e0f0")
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    # 经验-薪资关系
    if "experience" in filtered_df.columns:
        exp_data = (
            filtered_df.groupby("experience")
            .agg(岗位数=("job_title", "count"), 平均薪资=("salary_avg", "mean"))
            .reset_index()
        )
        exp_data = exp_data[exp_data["experience"] != "不限"]

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=exp_data["experience"], y=exp_data["岗位数"], name="岗位数",
                   marker_color="#7c3aed", opacity=0.8),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=exp_data["experience"], y=exp_data["平均薪资"], name="平均薪资(K)",
                       mode="lines+markers", line=dict(color="#10b981", width=3),
                       marker=dict(size=10)),
            secondary_y=True,
        )
        fig.update_layout(
            title="经验要求与薪资关系",
            height=450, hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0f0", legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        fig.update_yaxes(title_text="岗位数", secondary_y=False)
        fig.update_yaxes(title_text="平均薪资(K/月)", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# Tab 2: 薪资分析
# =========================================================================
with tab2:
    st.subheader("薪资深度分析")

    col_a, col_b = st.columns(2)

    with col_a:
        # 薪资直方图
        sal_data = filtered_df[filtered_df["salary_avg"] > 0]["salary_avg"]
        fig = px.histogram(
            sal_data, nbins=35, marginal="box",
            title="薪资分布直方图 (带箱线图)",
            color_discrete_sequence=["#7c3aed"],
            labels={"value": "月薪(K)", "count": "岗位数"},
        )
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="#e0e0f0")
        fig.add_vline(x=sal_data.mean(), line_dash="dash", line_color="#ef4444",
                      annotation_text=f"均值:{sal_data.mean():.1f}K")
        fig.add_vline(x=sal_data.median(), line_dash="dash", line_color="#10b981",
                      annotation_text=f"中位数:{sal_data.median():.1f}K")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # 城市薪资对比
        city_salary = (
            filtered_df.groupby("city")
            .agg(岗位数=("job_title", "count"), 平均薪资=("salary_avg", "mean"))
            .query("岗位数 >= 3")
            .sort_values("平均薪资", ascending=True)
        )
        fig = px.bar(
            x=city_salary["平均薪资"], y=city_salary.index,
            orientation="h", color=city_salary["平均薪资"],
            color_continuous_scale="RdYlGn",
            title="城市薪资对比 (岗位≥3)",
            labels={"x": "平均月薪(K)", "y": ""},
            text=city_salary["平均薪资"].round(1),
        )
        fig.update_traces(texttemplate="%{text}K", textposition="outside")
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="#e0e0f0")
        st.plotly_chart(fig, use_container_width=True)

    # 公司规模-薪资
    if "company_size" in filtered_df.columns:
        cs_data = (
            filtered_df[filtered_df["company_size"] != "未知"]
            .groupby("company_size")
            .agg(平均薪资=("salary_avg", "mean"), 最高薪资=("salary_max", "max"))
            .reset_index()
        )
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cs_data["company_size"], y=cs_data["平均薪资"], name="平均薪资",
                             marker_color="#7c3aed"))
        fig.add_trace(go.Bar(x=cs_data["company_size"], y=cs_data["最高薪资"], name="最高薪资",
                             marker_color="#06b6d4"))
        fig.update_layout(
            title="公司规模与薪资", barmode="group", height=400,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0f0", legend=dict(orientation="h", y=1.05),
        )
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# Tab 3: 技能与行业
# =========================================================================
with tab3:
    st.subheader("技能需求与行业分析")

    col_a, col_b = st.columns([1.5, 1])

    with col_a:
        # 技能频次 Top20
        counter = Counter()
        for skills_str in filtered_df.get("extracted_skills", pd.Series()).dropna():
            if skills_str and isinstance(skills_str, str):
                for s in skills_str.split("，"):
                    s = s.strip()
                    if s and len(s) > 1:
                        counter[s] += 1
        top = counter.most_common(20)
        if top:
            skills, counts = zip(*top)
            fig = px.bar(
                x=counts, y=skills, orientation="h",
                title="热门技能 Top20",
                color=counts, color_continuous_scale="Plasma",
                labels={"x": "出现频次", "y": ""},
            )
            fig.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="#e0e0f0")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # 行业需求
        ind_counts = filtered_df[filtered_df["industry"] != "未知"]["industry"].value_counts().head(12)
        fig = px.pie(
            values=ind_counts.values, names=ind_counts.index,
            title="行业需求分布 Top12",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
        fig.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", font_color="#e0e0f0")
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    # 行业薪资雷达图风格展示（用平行坐标替代，plotly 原生支持更好）
    ind_salary = (
        filtered_df[filtered_df["industry"] != "未知"]
        .groupby("industry")
        .agg(岗位数=("job_title", "count"), 平均薪资=("salary_avg", "mean"),
             最高薪资=("salary_max", "max"))
        .query("岗位数 >= 3")
        .sort_values("平均薪资", ascending=False)
        .head(10)
        .reset_index()
    )
    fig = px.scatter(
        ind_salary, x="平均薪资", y="岗位数", size="最高薪资",
        color="industry", text="industry", size_max=40,
        title="行业薪资-岗位气泡图",
        labels={"平均薪资": "平均月薪(K)", "岗位数": "岗位数量"},
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                     font_color="#e0e0f0", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# Tab 4: AI 专项对比
# =========================================================================
with tab4:
    st.subheader("AI 岗位 vs 非AI 岗位专项对比")

    if "is_ai_position" not in filtered_df.columns:
        st.warning("当前数据缺少 AI 岗位分类，请使用更新后的数据进行筛选。")
    else:
        ai = filtered_df[filtered_df["is_ai_position"] == "是"]
        non_ai = filtered_df[filtered_df["is_ai_position"] == "否"]

        # KPI 对比
        c1, c2, c3, c4, c5 = st.columns(5)
        ai_avg = ai[ai["salary_avg"] > 0]["salary_avg"].mean()
        non_avg = non_ai[non_ai["salary_avg"] > 0]["salary_avg"].mean()
        premium = ((ai_avg - non_avg) / non_avg * 100) if non_avg > 0 else 0

        c1.metric("AI岗位数", str(len(ai)))
        c2.metric("AI平均薪资", f"{ai_avg:.1f}K", delta=f"+{premium:.0f}%")
        c3.metric("非AI平均薪资", f"{non_avg:.1f}K")
        c4.metric("薪资溢价", f"{premium:.0f}%")
        c5.metric("AI占比", f"{len(ai)/max(len(filtered_df),1)*100:.1f}%")

        st.markdown("---")

        col_a, col_b = st.columns(2)

        with col_a:
            # AI城市分布
            ai_cities = ai["city"].value_counts().head(10)
            fig = px.bar(
                x=ai_cities.values, y=ai_cities.index, orientation="h",
                title="AI 岗位城市分布 Top10",
                color=ai_cities.values, color_continuous_scale="Plasma",
                labels={"x": "岗位数", "y": ""},
            )
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="#e0e0f0")
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            # AI学历要求
            ai_edu = ai["education"].value_counts()
            non_edu = non_ai["education"].value_counts()
            edu_compare = pd.DataFrame({"AI岗位": ai_edu, "非AI岗位": non_edu}).fillna(0)
            fig = go.Figure()
            fig.add_trace(go.Bar(y=edu_compare.index, x=edu_compare["AI岗位"], name="AI岗位",
                                orientation="h", marker_color="#7c3aed"))
            fig.add_trace(go.Bar(y=edu_compare.index, x=edu_compare["非AI岗位"], name="非AI岗位",
                                orientation="h", marker_color="#06b6d4"))
            fig.update_layout(
                title="学历要求对比: AI vs 非AI", barmode="group", height=400,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0f0", legend=dict(orientation="h", y=1.05),
            )
            st.plotly_chart(fig, use_container_width=True)

        # 技能对比
        col_a, col_b = st.columns(2)
        with col_a:
            ai_counter = Counter()
            for s_str in ai.get("extracted_skills", pd.Series()).dropna():
                if s_str and isinstance(s_str, str):
                    for s in s_str.split("，"):
                        if s.strip():
                            ai_counter[s.strip()] += 1
            top_ai = ai_counter.most_common(15)
            if top_ai:
                skills, counts = zip(*top_ai)
                fig = px.bar(x=counts, y=skills, orientation="h", title="AI岗位热门技能 Top15",
                            color=counts, color_continuous_scale="Plasma")
                fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 font_color="#e0e0f0")
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            non_counter = Counter()
            for s_str in non_ai.get("extracted_skills", pd.Series()).dropna():
                if s_str and isinstance(s_str, str):
                    for s in s_str.split("，"):
                        if s.strip():
                            non_counter[s.strip()] += 1
            top_non = non_counter.most_common(15)
            if top_non:
                skills, counts = zip(*top_non)
                fig = px.bar(x=counts, y=skills, orientation="h", title="非AI岗位热门技能 Top15",
                            color=counts, color_continuous_scale="Plasma")
                fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 font_color="#e0e0f0")
                st.plotly_chart(fig, use_container_width=True)


# ---- 底部工具栏 ----
st.markdown("---")
col_export, col_report, col_info = st.columns([1, 1, 3])

with col_export:
    csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="导出 CSV", data=csv, file_name=f"job_data_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

with col_report:
    if st.button("生成分析报告"):
        with st.spinner("正在生成报告..."):
            from modules.visualization import JobVisualizer
            viz = JobVisualizer(filtered_df)
            path = ReportGenerator(filtered_df, viz).generate()
            st.success(f"报告已生成: {path}")
            st.info("报告文件位于项目 data/report.html，在浏览器中打开即可查看。")

with col_info:
    st.caption("AI时代技术人才招聘市场洞察系统 v2.0 | 数据来源: 51job + 模拟数据 | 技术栈: Python + Streamlit + Plotly")


# ---- 启动说明（首次运行时显示） ----
if __name__ == "__main__":
    print("启动 Streamlit Web 应用...")
    print("请在终端运行: streamlit run web_app.py")
