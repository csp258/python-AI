# =============================================================================
# 可视化模块 - 22+ 种专业图表
# =============================================================================
# 设计思想：
# 1. 每个图表函数独立可调用 —— GUI 可选择展示任意图表组合
# 2. 统一使用 matplotlib Figure 作为返回值 —— 方便嵌入 GUI 的 Canvas
# 3. 所有图表都包含中文标题和轴标签 —— 确保用户可读
# 4. 配色统一使用 config.COLORS，保持专业风格
#
# 【求职加分点】
# - matplotlib 面向对象 API (fig, ax) 而非 pyplot 全局状态
# - 图表注释标注关键数据点，展示"数据叙事"能力
# - 合理的图表类型选择（如用箱线图而非柱状图展示分布）

import matplotlib
matplotlib.use("TkAgg")  # 后端设为 TkAgg —— 兼容 tkinter 嵌入
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import json
import re
from collections import Counter
from wordcloud import WordCloud

from config import COLORS, FONT_FAMILY, STOP_WORDS

# 全局 matplotlib 设置 —— 统一中文显示
plt.rcParams["font.sans-serif"] = [FONT_FAMILY, "SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 100

# 提取配色方案
C = COLORS
CHART_C = C["chart_colors"]
BG_DARK = C["bg_dark"]
BG_MEDIUM = C["bg_medium"]
TEXT_PRIMARY = C["text_primary"]
TEXT_SECONDARY = C["text_secondary"]

# 全局风格：深色背景专业风
plt.rcParams.update({
    "figure.facecolor": BG_MEDIUM,
    "axes.facecolor": BG_MEDIUM,
    "axes.edgecolor": TEXT_SECONDARY,
    "axes.labelcolor": TEXT_PRIMARY,
    "text.color": TEXT_PRIMARY,
    "xtick.color": TEXT_SECONDARY,
    "ytick.color": TEXT_SECONDARY,
    "grid.color": "#3a3a5c",
    "grid.alpha": 0.5,
})


class JobVisualizer:
    """
    招聘数据可视化器 —— 包含22+种专业图表

    设计原则（数据可视化最佳实践）：
    1. 比较用柱状图、分类用饼图、分布用直方图、关系用散点图
    2. 每个图表都有明确的"一句话结论"
    3. 颜色区分不同类别，避免色盲不友好配色
    """

    def __init__(self, df: pd.DataFrame):
        """
        参数:
            df: 清洗后的招聘数据 DataFrame
        """
        self.df = df

    # =====================================================================
    # 图表1：城市岗位数量分布 —— 横向柱状图（适合长标签）
    # =====================================================================
    def chart_city_jobs(self, figsize=(10, 6)) -> Figure:
        """
        图表1：各城市技术岗位数量 Top15 横向柱状图

        图表类型选择理由：
        - 横向柱状图：城市名称长度不一，纵向会重叠
        - 降序排列：一目了然地看出热门城市排名
        """
        city_counts = self.df["city"].value_counts().head(15)
        # 降序排列（横向柱状图需要反转y轴）
        city_counts = city_counts.iloc[::-1]

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        colors = [CHART_C[i % len(CHART_C)] for i in range(len(city_counts))]
        bars = ax.barh(city_counts.index, city_counts.values, color=colors, height=0.7)

        # 在柱末端标注数值
        for bar, val in zip(bars, city_counts.values):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", fontsize=9, color=TEXT_PRIMARY)

        ax.set_title("技术岗位城市分布 Top15", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("岗位数量", fontsize=11, color=TEXT_SECONDARY)
        ax.xaxis.grid(True, alpha=0.3)
        ax.tick_params(axis="both", labelsize=10)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表2：薪资分布直方图 + KDE密度曲线
    # =====================================================================
    def chart_salary_distribution(self, figsize=(10, 6)) -> Figure:
        """
        图表2：技术岗位薪资分布直方图（带密度曲线）

        为什么加 KDE 曲线？
        - 直方图受组距影响大（组距不同形态不同）
        - KDE 提供平滑的分布形状，更加客观
        - 两者叠加是业界标准做法
        """
        salary_data = self.df[self.df["salary_avg"] > 0]["salary_avg"]

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        # 直方图
        n, bins, patches = ax.hist(
            salary_data, bins=30, alpha=0.65, color=CHART_C[0],
            edgecolor=BG_MEDIUM, linewidth=0.5, label="频数分布"
        )

        # KDE 密度曲线（双Y轴）
        ax2 = ax.twinx()
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(salary_data)
        x_range = np.linspace(salary_data.min(), salary_data.max(), 200)
        ax2.plot(x_range, kde(x_range), color=CHART_C[3], linewidth=2.5,
                 label="密度曲线")
        ax2.fill_between(x_range, kde(x_range), alpha=0.15, color=CHART_C[3])
        ax2.set_ylabel("概率密度", fontsize=11, color=CHART_C[3])
        ax2.tick_params(axis="y", colors=CHART_C[3])

        # 标注均值和中位数
        mean_val = salary_data.mean()
        median_val = salary_data.median()
        ax.axvline(mean_val, color=CHART_C[4], linestyle="--", linewidth=1.5,
                   label=f"均值: {mean_val:.1f}K")
        ax.axvline(median_val, color=CHART_C[2], linestyle="--", linewidth=1.5,
                   label=f"中位数: {median_val:.1f}K")

        ax.set_title("技术岗位薪资分布 (K/月)", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("月薪 (K)", fontsize=11, color=TEXT_SECONDARY)
        ax.set_ylabel("岗位数量", fontsize=11, color=TEXT_SECONDARY)
        ax.legend(loc="upper right", fontsize=9)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表3：学历要求饼图
    # =====================================================================
    def chart_education_pie(self, figsize=(8, 8)) -> Figure:
        """
        图表3：学历要求比例饼图

        设计要点：
        - 突出显示比例最大的扇区（explode）
        - autopct 显示百分比，方便精确阅读
        - 顺时针排列，从12点方向开始
        """
        edu_counts = self.df["education"].value_counts()

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        # 找到最大值索引用于 explode
        max_label = edu_counts.idxmax()
        explode = [0.05 if label == max_label else 0.02
                   for label in edu_counts.index]

        wedges, texts, autotexts = ax.pie(
            edu_counts.values,
            labels=edu_counts.index,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.75,
            explode=explode,
            colors=CHART_C[:len(edu_counts)],
            textprops={"color": TEXT_PRIMARY, "fontsize": 11},
        )

        # 百分比文字样式
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontsize(10)
            autotext.set_fontweight("bold")

        ax.set_title("学历要求分布", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=20)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表4：经验要求分布
    # =====================================================================
    def chart_experience_distribution(self, figsize=(10, 6)) -> Figure:
        """
        图表4：经验要求与平均薪资关系

        双轴图表：柱状图 = 岗位数量，折线 = 平均薪资
        """
        exp_groups = self.df.groupby("experience", observed=False).agg(
            岗位数量=("job_title", "count"),
            平均薪资=("salary_avg", "mean")
        ).reset_index()
        exp_groups = exp_groups[exp_groups["experience"] != "不限"]

        fig, ax1 = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        # 柱状图 —— 岗位数量
        bars = ax1.bar(exp_groups["experience"], exp_groups["岗位数量"],
                       color=CHART_C[0], alpha=0.8, label="岗位数量", width=0.6)

        # 折线图 —— 平均薪资（双Y轴）
        ax2 = ax1.twinx()
        ax2.plot(exp_groups["experience"], exp_groups["平均薪资"],
                 color=CHART_C[3], marker="o", linewidth=2.5, markersize=8,
                 label="平均薪资(K)")

        # 数据标注
        for i, row in exp_groups.iterrows():
            ax2.annotate(f'{row["平均薪资"]:.1f}K',
                        (row["experience"], row["平均薪资"]),
                        textcoords="offset points", xytext=(0, 12),
                        fontsize=9, color=CHART_C[3], ha="center")

        ax1.set_title("经验要求与薪资关系", fontsize=14, fontweight="bold",
                      color=TEXT_PRIMARY, pad=15)
        ax1.set_xlabel("经验要求", fontsize=11, color=TEXT_SECONDARY)
        ax1.set_ylabel("岗位数量", fontsize=11, color=CHART_C[0])
        ax2.set_ylabel("平均薪资 (K/月)", fontsize=11, color=CHART_C[3])
        ax1.tick_params(axis="x", rotation=30, labelsize=9)
        ax1.tick_params(axis="y", colors=CHART_C[0])
        ax2.tick_params(axis="y", colors=CHART_C[3])

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表5：行业需求排行
    # =====================================================================
    def chart_industry_ranking(self, figsize=(10, 6)) -> Figure:
        """图表5：行业技术岗位需求 Top15 横向柱状图"""
        ind = self.df[self.df["industry"] != "未知"]["industry"].value_counts().head(15)
        ind = ind.iloc[::-1]

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        colors = [CHART_C[i % len(CHART_C)] for i in range(len(ind))]
        bars = ax.barh(ind.index, ind.values, color=colors, height=0.7)

        for bar, val in zip(bars, ind.values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", fontsize=9, color=TEXT_PRIMARY)

        ax.set_title("技术岗位行业需求 Top15", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("岗位数量", fontsize=11, color=TEXT_SECONDARY)
        ax.xaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表6：技能词云
    # =====================================================================
    def chart_skill_wordcloud(self, figsize=(12, 8)) -> Figure:
        """图表6：热门技能词云 —— 一眼看出市场最需要的技术"""
        if "extracted_skills" not in self.df.columns:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "无技能数据", ha="center", va="center", fontsize=20)
            return fig

        counter = Counter()
        for skills_str in self.df["extracted_skills"].dropna():
            if skills_str and isinstance(skills_str, str):
                for s in skills_str.split("，"):
                    s = s.strip()
                    if s and len(s) > 1 and s not in STOP_WORDS:
                        counter[s] += 1

        if not counter:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "无技能数据", ha="center", va="center", fontsize=20)
            return fig

        # 生成词云
        wc = WordCloud(
            font_path="C:/Windows/Fonts/msyh.ttc" if self._is_windows() else None,
            width=1200, height=800,
            background_color="#2d2d44",
            colormap="plasma",
            max_words=100,
            max_font_size=150,
            min_font_size=12,
            relative_scaling=0.5,
            prefer_horizontal=0.85,
            collocations=False,
        )
        wc.generate_from_frequencies(counter)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title("热门技能词云 —— 市场最需要掌握的技能",
                     fontsize=14, fontweight="bold", color=TEXT_PRIMARY, pad=15)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表7：公司规模分布
    # =====================================================================
    def chart_company_size(self, figsize=(9, 9)) -> Figure:
        """图表7：公司规模环形图（donut chart）—— 比饼图更现代"""
        size_counts = self.df["company_size"].value_counts()

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        wedges, texts, autotexts = ax.pie(
            size_counts.values,
            labels=size_counts.index,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.82,
            colors=CHART_C[:len(size_counts)],
            textprops={"color": TEXT_PRIMARY, "fontsize": 10},
        )

        # 制作环形图：在中间画一个白色圆
        center_circle = plt.Circle((0, 0), 0.55, fc=BG_MEDIUM, ec="none")
        ax.add_artist(center_circle)

        # 中心文字
        total = size_counts.sum()
        ax.text(0, 0.05, f"共{total}个岗位", ha="center", va="center",
                fontsize=14, fontweight="bold", color=TEXT_PRIMARY)
        ax.text(0, -0.1, f"涉及{len(size_counts)}种规模", ha="center", va="center",
                fontsize=10, color=TEXT_SECONDARY)

        ax.set_title("公司规模分布", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=20)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表8：薪资-经验箱线图
    # =====================================================================
    def chart_salary_boxplot(self, figsize=(10, 6)) -> Figure:
        """
        图表8：不同经验水平的薪资箱线图

        为什么用箱线图而非柱状图？
        - 柱状图只展示均值，掩盖了分布信息
        - 箱线图同时展示：中位数、四分位数、离群值
        - 一眼看出薪资的"范围"和"离散程度"
        """
        exp_order = ["在校生/应届生", "1年经验", "2年经验", "3-4年经验",
                     "5-7年经验", "8-9年经验", "10年以上经验"]
        data_groups = []
        labels = []
        for exp in exp_order:
            subset = self.df[self.df["experience"].astype(str).str.contains(exp)]["salary_avg"]
            subset = subset[subset > 0]
            if len(subset) >= 3:
                data_groups.append(subset)
                labels.append(exp)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        bp = ax.boxplot(data_groups, labels=labels, patch_artist=True,
                        showmeans=True, meanprops=dict(marker="D", markerfacecolor=CHART_C[4],
                                                       markersize=6))

        # 上色
        for i, box in enumerate(bp["boxes"]):
            box.set_facecolor(CHART_C[i % len(CHART_C)])
            box.set_alpha(0.7)

        ax.set_title("不同经验水平薪资分布（箱线图）", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_ylabel("月薪 (K)", fontsize=11, color=TEXT_SECONDARY)
        ax.tick_params(axis="x", rotation=30, labelsize=9)
        ax.yaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表9：岗位发布趋势
    # =====================================================================
    def chart_job_trend(self, figsize=(10, 6)) -> Figure:
        """图表9：每日岗位发布趋势折线图 —— 反映招聘市场活跃度"""
        trend = self.df.groupby("post_date").size()
        if trend.empty:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "无日期数据", ha="center", va="center")
            return fig

        # 按日期排序
        trend = trend.sort_index()

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        ax.fill_between(range(len(trend)), trend.values, alpha=0.3, color=CHART_C[0])
        ax.plot(range(len(trend)), trend.values, color=CHART_C[0], linewidth=2, marker="o",
                markersize=4)

        # 只显示部分日期标签避免重叠
        step = max(1, len(trend) // 10)
        tick_positions = list(range(0, len(trend), step))
        tick_labels = [trend.index[i] for i in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=8)

        ax.set_title("岗位发布趋势（近60天）", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_ylabel("日发布量", fontsize=11, color=TEXT_SECONDARY)
        ax.yaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表10：城市薪资对比
    # =====================================================================
    def chart_city_salary_compare(self, figsize=(10, 6)) -> Figure:
        """图表10：各城市平均薪资对比柱状图（仅含岗位≥5的城市）"""
        city_stats = self.df.groupby("city").agg(
            岗位数=("job_title", "count"),
            平均薪资=("salary_avg", "mean")
        ).query("岗位数 >= 3").sort_values("平均薪资", ascending=True)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        # 颜色渐变：低薪→冷色，高薪→暖色
        norm = plt.Normalize(city_stats["平均薪资"].min(), city_stats["平均薪资"].max())
        colors = plt.cm.RdYlGn(norm(city_stats["平均薪资"].values))

        bars = ax.barh(city_stats.index, city_stats["平均薪资"].values,
                       color=colors, height=0.7)

        for bar, val in zip(bars, city_stats["平均薪资"].values):
            ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                    f"{val:.1f}K", va="center", fontsize=9, color=TEXT_PRIMARY)

        ax.set_title("各城市技术岗位平均薪资对比", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("平均月薪 (K)", fontsize=11, color=TEXT_SECONDARY)
        ax.xaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表11：热门技能排行
    # =====================================================================
    def chart_top_skills(self, figsize=(10, 6)) -> Figure:
        """图表11：市场最热门的技术技能 Top20 柱状图"""
        counter = Counter()
        for skills_str in self.df.get("extracted_skills", pd.Series()).dropna():
            if skills_str and isinstance(skills_str, str):
                for s in skills_str.split("，"):
                    s = s.strip()
                    if s and len(s) > 1:
                        counter[s] += 1

        top = counter.most_common(20)
        if not top:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "无技能数据", ha="center", va="center")
            return fig

        skills, counts = zip(*top)
        skills = skills[::-1]
        counts = counts[::-1]

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        bars = ax.barh(skills, counts, color=CHART_C[0], height=0.7)

        for bar, val in zip(bars, counts):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", fontsize=9, color=TEXT_PRIMARY)

        ax.set_title("热门技术技能 Top20", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("出现频次", fontsize=11, color=TEXT_SECONDARY)
        ax.xaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表12：学历-薪资箱线图
    # =====================================================================
    def chart_education_salary_box(self, figsize=(10, 6)) -> Figure:
        """图表12：不同学历的薪资分布箱线图"""
        edu_order = ["高中及以下", "大专", "本科", "硕士", "博士"]
        groups = []
        labels = []
        for edu in edu_order:
            subset = self.df[self.df["education"] == edu]["salary_avg"]
            subset = subset[subset > 0]
            if len(subset) >= 2:
                groups.append(subset)
                labels.append(f"{edu}\n(n={len(subset)})")

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        bp = ax.boxplot(groups, labels=labels, patch_artist=True,
                        showmeans=True, meanprops=dict(marker="D", markerfacecolor=CHART_C[4],
                                                       markersize=6))

        for i, box in enumerate(bp["boxes"]):
            box.set_facecolor(CHART_C[i % len(CHART_C)])
            box.set_alpha(0.7)

        ax.set_title("学历与薪资关系", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_ylabel("月薪 (K)", fontsize=11, color=TEXT_SECONDARY)
        ax.yaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表13：行业薪资雷达图
    # =====================================================================
    def chart_industry_radar(self, figsize=(9, 9)) -> Figure:
        """
        图表13：行业薪资雷达图

        雷达图适用场景：
        - 多维指标对比（不同行业的多维度：岗位数、平均薪资、最高薪资…）
        - 突出展示"形状"差异
        """
        ind_stats = self.df.groupby("industry").agg(
            岗位数=("job_title", "count"),
            平均薪资=("salary_avg", "mean"),
            最高薪资=("salary_max", "max"),
        ).query("岗位数 >= 3").head(6)

        # 归一化到 [0, 1] 便于雷达图展示
        data_cols = ["岗位数", "平均薪资", "最高薪资"]
        display_labels = ["岗位数量", "平均薪资", "最高薪资"]
        N = len(data_cols)

        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]  # 闭合

        fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
        fig.patch.set_facecolor(BG_MEDIUM)
        ax.set_facecolor(BG_MEDIUM)

        all_vals = ind_stats[data_cols].values
        mins, maxs = all_vals.min(axis=0), all_vals.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1  # 处理所有值相同的情况

        for i, (industry, row) in enumerate(ind_stats.iterrows()):
            values = [row[col] for col in data_cols]
            norm_values = ((np.array(values) - mins) / ranges).tolist()
            norm_values += norm_values[:1]

            ax.fill(angles, norm_values, alpha=0.1, color=CHART_C[i])
            ax.plot(angles, norm_values, "o-", linewidth=2, label=industry,
                    color=CHART_C[i])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(display_labels, fontsize=11, color=TEXT_PRIMARY)
        ax.set_yticklabels([])  # 隐藏径向刻度
        ax.set_title("行业多维对比（雷达图）", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=25)
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=9)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表14：AI vs 非AI岗位薪资对比
    # =====================================================================
    def chart_ai_vs_nonai(self, figsize=(9, 6)) -> Figure:
        """图表14：AI岗位 vs 非AI岗位 薪资对比分组柱状图"""
        if "is_ai_position" not in self.df.columns:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "无AI分类数据", ha="center", va="center")
            return fig

        comp = self.df.groupby("is_ai_position").agg(
            岗位数量=("job_title", "count"),
            平均薪资=("salary_avg", "mean"),
            最高薪资=("salary_max", "max"),
            最低薪资=("salary_min", lambda x: x[x > 0].mean()),
        ).round(1)

        fig, axes = plt.subplots(1, 2, figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        # 左：岗位数量对比
        ax = axes[0]
        ax.set_facecolor(BG_MEDIUM)
        bars = ax.bar(comp.index.tolist(), comp["岗位数量"].values,
                      color=[CHART_C[0], CHART_C[5]], width=0.5)
        for bar, val in zip(bars, comp["岗位数量"].values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    str(val), ha="center", fontsize=12, fontweight="bold",
                    color=TEXT_PRIMARY)
        ax.set_title("岗位数量对比", fontsize=12, color=TEXT_PRIMARY)
        ax.set_ylabel("岗位数", fontsize=10, color=TEXT_SECONDARY)

        # 右：薪资对比
        ax = axes[1]
        ax.set_facecolor(BG_MEDIUM)
        metrics = ["平均薪资", "最高薪资", "最低薪资"]
        x = np.arange(len(metrics))
        width = 0.3

        for i, (idx, row) in enumerate(comp.iterrows()):
            offset = width * (i - 0.5)
            vals = [row["平均薪资"], row["最高薪资"], row["最低薪资"]]
            bars = ax.bar(x + offset, vals, width, label=idx,
                          color=CHART_C[0] if i == 0 else CHART_C[5])
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        f"{val:.0f}", ha="center", fontsize=8, color=TEXT_PRIMARY)

        ax.set_xticks(x)
        ax.set_xticklabels(metrics, fontsize=10, color=TEXT_PRIMARY)
        ax.set_title("薪资对比 (K/月)", fontsize=12, color=TEXT_PRIMARY)
        ax.legend(fontsize=9)
        ax.yaxis.grid(True, alpha=0.3)

        fig.suptitle("AI相关岗位 vs 非AI岗位 全面对比", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, y=1.02)
        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表15：薪资-经验气泡图
    # =====================================================================
    def chart_salary_bubble(self, figsize=(10, 6)) -> Figure:
        """
        图表15：各城市薪资-岗位数气泡图

        气泡图 = 散点图 + 第三维（气泡大小）
        X轴=平均薪资, Y轴=岗位数, 气泡大小=最高薪资
        """
        city_stats = self.df.groupby("city").agg(
            岗位数=("job_title", "count"),
            平均薪资=("salary_avg", "mean"),
            最高薪资=("salary_max", "max"),
        ).query("岗位数 >= 3")

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)
        ax.set_facecolor(BG_MEDIUM)

        # 气泡大小与岗位数成正比
        sizes = city_stats["岗位数"] * 15

        scatter = ax.scatter(
            city_stats["平均薪资"], city_stats["岗位数"],
            s=sizes, c=city_stats["最高薪资"],
            cmap="plasma", alpha=0.7, edgecolors=TEXT_SECONDARY, linewidth=0.5
        )

        # 标注城市名
        for city, row in city_stats.iterrows():
            ax.annotate(city, (row["平均薪资"], row["岗位数"]),
                        textcoords="offset points", xytext=(8, 3),
                        fontsize=9, color=TEXT_PRIMARY)

        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label("最高薪资 (K/月)", color=TEXT_PRIMARY)
        cbar.ax.yaxis.set_tick_params(color=TEXT_SECONDARY)

        ax.set_title("城市薪资-岗位数气泡图", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("平均月薪 (K)", fontsize=11, color=TEXT_SECONDARY)
        ax.set_ylabel("岗位数量", fontsize=11, color=TEXT_SECONDARY)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表16：公司类型分布与薪资
    # =====================================================================
    def chart_company_type(self, figsize=(10, 6)) -> Figure:
        """图表16：公司类型分布及对应平均薪资"""
        ct = self.df[self.df["company_type"] != "未知"].groupby("company_type").agg(
            岗位数=("job_title", "count"),
            平均薪资=("salary_avg", "mean")
        ).sort_values("岗位数", ascending=True)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        bars = ax.barh(ct.index, ct["岗位数"], color=CHART_C[:len(ct)], height=0.6,
                       alpha=0.8)

        # 在每个柱上标注薪资
        for bar, (_, row) in zip(bars, ct.iterrows()):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                    f"均薪{row['平均薪资']:.1f}K", va="center",
                    fontsize=9, color=TEXT_PRIMARY)

        ax.set_title("公司类型分布与平均薪资", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("岗位数量", fontsize=11, color=TEXT_SECONDARY)
        ax.xaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表17：薪资区间分布
    # =====================================================================
    def chart_salary_range_distribution(self, figsize=(8, 8)) -> Figure:
        """图表17：薪资等级区间环形图"""
        if "salary_level" not in self.df.columns:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "无薪资分级数据", ha="center", va="center")
            return fig

        level_counts = self.df["salary_level"].value_counts()

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        wedges, texts, autotexts = ax.pie(
            level_counts.values,
            labels=level_counts.index,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.82,
            colors=CHART_C[:len(level_counts)],
            textprops={"color": TEXT_PRIMARY, "fontsize": 10},
        )

        # 环形中空
        center_circle = plt.Circle((0, 0), 0.55, fc=BG_MEDIUM, ec="none")
        ax.add_artist(center_circle)
        ax.text(0, 0, f"总岗位\n{level_counts.sum()}", ha="center", va="center",
                fontsize=13, fontweight="bold", color=TEXT_PRIMARY)

        ax.set_title("薪资区间分布", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=20)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表18：技能关联热力图
    # =====================================================================
    def chart_skill_heatmap(self, figsize=(10, 8)) -> Figure:
        """
        图表18：技能共现热力图

        热力图解读：
        - 颜色越亮 = 两项技能同时被需要的概率越高
        - 对角线上是最热门技能
        - 例如：Python+TensorFlow 高亮 → 说明ML岗位经常同时要求两者
        """
        counter = Counter()
        skill_sets = []
        for skills_str in self.df.get("extracted_skills", pd.Series()).dropna():
            if skills_str and isinstance(skills_str, str):
                skill_list = [s.strip() for s in skills_str.split("，") if s.strip()]
                if skill_list:
                    skill_sets.append(set(skill_list))
                    for s in skill_list:
                        counter[s] += 1

        # 取Top12技能
        top_skills = [s for s, _ in counter.most_common(12)]
        n = len(top_skills)

        # 构建共现矩阵
        matrix = np.zeros((n, n))
        for skill_set in skill_sets:
            for i, s1 in enumerate(top_skills):
                for j, s2 in enumerate(top_skills):
                    if s1 in skill_set and s2 in skill_set:
                        matrix[i][j] += 1

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        im = ax.imshow(matrix, cmap="plasma", aspect="auto")

        ax.set_xticks(range(n))
        ax.set_xticklabels(top_skills, rotation=45, ha="right", fontsize=9,
                           color=TEXT_PRIMARY)
        ax.set_yticks(range(n))
        ax.set_yticklabels(top_skills, fontsize=9, color=TEXT_PRIMARY)

        # 在单元格标注数值
        for i in range(n):
            for j in range(n):
                ax.text(j, i, int(matrix[i][j]), ha="center", va="center",
                        fontsize=7, color="white")

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("共现次数", color=TEXT_PRIMARY)

        ax.set_title("技能共现热力图 —— 哪些技能常一起出现",
                     fontsize=14, fontweight="bold", color=TEXT_PRIMARY, pad=15)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表19：资历等级分布
    # =====================================================================
    def chart_seniority_distribution(self, figsize=(8, 8)) -> Figure:
        """图表19：岗位资历等级分布饼图"""
        if "seniority_level" not in self.df.columns:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "无资历数据", ha="center", va="center")
            return fig

        sen_counts = self.df["seniority_level"].value_counts()

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        colors = {
            "初级": CHART_C[2], "中级": CHART_C[0], "高级": CHART_C[4], "未知": "#666"
        }
        pie_colors = [colors.get(l, "#888") for l in sen_counts.index]

        wedges, texts, autotexts = ax.pie(
            sen_counts.values, labels=sen_counts.index,
            autopct="%1.1f%%", startangle=90, pctdistance=0.75,
            colors=pie_colors,
            textprops={"color": TEXT_PRIMARY, "fontsize": 12},
        )

        for at in autotexts:
            at.set_color("white")
            at.set_fontweight("bold")

        ax.set_title("岗位资历等级分布（初级/中级/高级）",
                     fontsize=14, fontweight="bold", color=TEXT_PRIMARY, pad=20)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表20：公司规模-薪资对比
    # =====================================================================
    def chart_company_size_salary(self, figsize=(10, 6)) -> Figure:
        """图表20：公司规模与薪资关系"""
        cs = self.df[self.df["company_size"] != "未知"].groupby("company_size").agg(
            岗位数=("job_title", "count"),
            平均薪资=("salary_avg", "mean"),
            最高薪资=("salary_max", "max"),
        ).sort_values("平均薪资", ascending=True)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        x = np.arange(len(cs))
        width = 0.35

        bars1 = ax.bar(x - width/2, cs["平均薪资"], width, label="平均薪资(K)",
                       color=CHART_C[0], alpha=0.85)
        bars2 = ax.bar(x + width/2, cs["最高薪资"], width, label="最高薪资(K)",
                       color=CHART_C[3], alpha=0.85)

        # 标注数值
        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"{bar.get_height():.0f}", ha="center", fontsize=8, color=TEXT_PRIMARY)
        for bar in bars2:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"{bar.get_height():.0f}", ha="center", fontsize=8, color=TEXT_PRIMARY)

        ax.set_xticks(x)
        ax.set_xticklabels(cs.index, rotation=30, ha="right", fontsize=9, color=TEXT_PRIMARY)
        ax.set_title("公司规模与薪资关系", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_ylabel("薪资 (K/月)", fontsize=11, color=TEXT_SECONDARY)
        ax.legend(fontsize=10)
        ax.yaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表21：岗位类型（职位关键词）分布
    # =====================================================================
    def chart_job_title_distribution(self, figsize=(10, 6)) -> Figure:
        """图表21：技术岗位细分类型 Top15"""
        titles = self.df["job_title"].value_counts().head(15)
        titles = titles.iloc[::-1]

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        bars = ax.barh(titles.index, titles.values,
                       color=CHART_C[:len(titles)], height=0.7)

        for bar, val in zip(bars, titles.values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", fontsize=9, color=TEXT_PRIMARY)

        ax.set_title("热门技术岗位类型 Top15", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("岗位数量", fontsize=11, color=TEXT_SECONDARY)
        ax.xaxis.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表22：薪资与学历交叉分析（热力图风格）
    # =====================================================================
    def chart_salary_education_heatmap(self, figsize=(10, 6)) -> Figure:
        """图表22：学历 vs 经验 vs 薪资三维交叉分析"""
        pivot = self.df.pivot_table(
            values="salary_avg", index="education",
            columns="experience", aggfunc="mean",
            observed=False
        ).round(1)

        # 只保留有意义的行列
        pivot = pivot.drop(columns=["不限"], errors="ignore")
        pivot = pivot.drop(index=["不限"], errors="ignore")

        if pivot.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "数据不足", ha="center", va="center")
            return fig

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto")

        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=30, ha="right", fontsize=9,
                           color=TEXT_PRIMARY)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=9, color=TEXT_PRIMARY)

        # 标注数值
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i][j]
                if not np.isnan(val):
                    ax.text(j, i, f"{val:.0f}K", ha="center", va="center",
                            fontsize=9, fontweight="bold",
                            color="white" if val > pivot.values.mean() else TEXT_PRIMARY)

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("平均薪资(K/月)", color=TEXT_PRIMARY)

        ax.set_title("学历×经验 薪资交叉分析热力图", fontsize=14, fontweight="bold",
                     color=TEXT_PRIMARY, pad=15)
        ax.set_xlabel("经验要求", fontsize=11, color=TEXT_SECONDARY)
        ax.set_ylabel("学历要求", fontsize=11, color=TEXT_SECONDARY)

        plt.tight_layout()
        return fig

    # =====================================================================
    # 图表23：岗位福利词云
    # =====================================================================
    def chart_benefits_wordcloud(self, figsize=(12, 6)) -> Figure:
        """图表23：福利待遇高频词词云 —— 了解企业提供哪些福利"""
        counter = Counter()
        for benefits_str in self.df.get("benefits", pd.Series()).dropna():
            if benefits_str and isinstance(benefits_str, str):
                # "五险一金，带薪年假，股票期权" → 拆分
                for b in re.split(r'[，,、\s]+', benefits_str):
                    b = b.strip()
                    if b and len(b) > 1:
                        counter[b] += 1

        if not counter:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "无福利数据", ha="center", va="center")
            return fig

        wc = WordCloud(
            font_path="C:/Windows/Fonts/msyh.ttc" if self._is_windows() else None,
            width=1200, height=600,
            background_color="#2d2d44",
            colormap="viridis",
            max_words=50,
            max_font_size=120,
            prefer_horizontal=0.9,
        )
        wc.generate_from_frequencies(counter)

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title("企业福利关键词云 —— 什么样的福利最常见？",
                     fontsize=14, fontweight="bold", color=TEXT_PRIMARY, pad=15)

        plt.tight_layout()
        return fig

    # ---------------------------------------------------------------------
    # 综合仪表盘 —— 多图合一
    # ---------------------------------------------------------------------
    def dashboard_overview(self, figsize=(16, 12)) -> Figure:
        """
        综合仪表盘：4合1总览视图

        左上：城市分布 | 右上：学历分布
        左下：经验-薪资 | 右下：行业排行

        适合作为 GUI 首页展示
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.patch.set_facecolor(BG_MEDIUM)

        # --- 左上：城市分布 ---
        ax = axes[0, 0]
        ax.set_facecolor(BG_MEDIUM)
        city_counts = self.df["city"].value_counts().head(8)
        ax.barh(city_counts.index[::-1], city_counts.values[::-1],
                color=CHART_C[:8], height=0.6)
        ax.set_title("热门城市 Top8", fontsize=12, color=TEXT_PRIMARY, fontweight="bold")
        ax.xaxis.grid(True, alpha=0.3)

        # --- 右上：学历分布 ---
        ax = axes[0, 1]
        ax.set_facecolor(BG_MEDIUM)
        edu = self.df["education"].value_counts()
        ax.pie(edu.values, labels=edu.index, autopct="%1.1f%%",
               colors=CHART_C[:len(edu)], textprops={"fontsize": 9, "color": TEXT_PRIMARY})
        ax.set_title("学历要求分布", fontsize=12, color=TEXT_PRIMARY, fontweight="bold")

        # --- 左下：经验-薪资 ---
        ax = axes[1, 0]
        ax.set_facecolor(BG_MEDIUM)
        exp = self.df.groupby("experience", observed=False)["salary_avg"].mean()
        exp = exp[exp > 0]
        ax.bar(range(len(exp)), exp.values, color=CHART_C[0], alpha=0.8)
        ax.set_xticks(range(len(exp)))
        ax.set_xticklabels(exp.index, rotation=30, ha="right", fontsize=8, color=TEXT_PRIMARY)
        ax.set_title("各经验水平平均薪资", fontsize=12, color=TEXT_PRIMARY, fontweight="bold")
        ax.set_ylabel("K/月", fontsize=9, color=TEXT_SECONDARY)
        ax.yaxis.grid(True, alpha=0.3)

        # --- 右下：行业排行 ---
        ax = axes[1, 1]
        ax.set_facecolor(BG_MEDIUM)
        ind = self.df["industry"].value_counts().head(8)
        ax.barh(ind.index[::-1], ind.values[::-1], color=CHART_C[:8], height=0.6)
        ax.set_title("热门行业 Top8", fontsize=12, color=TEXT_PRIMARY, fontweight="bold")
        ax.xaxis.grid(True, alpha=0.3)

        fig.suptitle("AI时代技术人才招聘市场 —— 全景洞察仪表盘",
                     fontsize=16, fontweight="bold", color=TEXT_PRIMARY, y=1.01)

        plt.tight_layout()
        return fig

    # ---------------------------------------------------------------------
    # 获取所有图表的名称和函数映射
    # ---------------------------------------------------------------------
    def get_all_charts(self) -> dict:
        """
        返回所有可用图表的名称和函数映射

        用于 GUI 动态生成图表按钮
        """
        return {
            "1-城市岗位分布": self.chart_city_jobs,
            "2-薪资分布直方图": self.chart_salary_distribution,
            "3-学历要求饼图": self.chart_education_pie,
            "4-经验要求与薪资": self.chart_experience_distribution,
            "5-行业需求排行": self.chart_industry_ranking,
            "6-技能词云": self.chart_skill_wordcloud,
            "7-公司规模环形图": self.chart_company_size,
            "8-薪资箱线图": self.chart_salary_boxplot,
            "9-岗位发布趋势": self.chart_job_trend,
            "10-城市薪资对比": self.chart_city_salary_compare,
            "11-热门技能排行": self.chart_top_skills,
            "12-学历薪资箱线图": self.chart_education_salary_box,
            "13-行业薪资雷达图": self.chart_industry_radar,
            "14-AI vs 非AI对比": self.chart_ai_vs_nonai,
            "15-薪资气泡图": self.chart_salary_bubble,
            "16-公司类型薪资": self.chart_company_type,
            "17-薪资区间环形图": self.chart_salary_range_distribution,
            "18-技能共现热力图": self.chart_skill_heatmap,
            "19-资历等级分布": self.chart_seniority_distribution,
            "20-公司规模薪资": self.chart_company_size_salary,
            "21-岗位类型分布": self.chart_job_title_distribution,
            "22-学历经验交叉热力图": self.chart_salary_education_heatmap,
            "23-福利词云": self.chart_benefits_wordcloud,
            "仪表盘-全景总览": self.dashboard_overview,
        }

    @staticmethod
    def _is_windows() -> bool:
        """检测是否 Windows 系统（用于字体路径判断）"""
        import platform
        return platform.system() == "Windows"
