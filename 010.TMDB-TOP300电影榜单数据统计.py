from pathlib import Path  # 导入路径处理模块，方便定位文件
import matplotlib  # 导入 matplotlib 绘图库
matplotlib.use("Agg")  # 使用非交互式后端，避免弹出显示窗口
import matplotlib.pyplot as plt  # 导入 pyplot 用于绘图
from matplotlib.axes import Axes  # 导入 Axes 类型，方便类型提示
import pandas as pd  # 导入 pandas 用于数据处理


plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置中文字体为黑体，避免乱码
plt.rcParams["axes.unicode_minus"] = False  # 使负号正常显示


def find_data_file(start_dir: Path | None = None) -> Path:
    """查找电影数据文件。"""
    if start_dir is None:  # 如果没有传入目录，就默认使用当前脚本所在目录
        start_dir = Path(__file__).resolve().parent  # 获取脚本所在目录的绝对路径

    candidates = [  # 定义可能的数据文件路径列表
        start_dir / "数据分析" / "素材" / "movies.csv",  # 课程资料目录中的数据文件
        start_dir / "素材" / "movies.csv",  # 当前目录下的素材文件
    ]

    for path in candidates:  # 遍历所有候选路径
        if path.exists():  # 如果文件存在，就返回这个路径
            return path

    raise FileNotFoundError(f"未找到电影数据文件，请检查路径。候选路径：{candidates}")  # 如果都没找到，就报错


def load_movie_data(csv_path: Path) -> pd.DataFrame:
    """读取并清洗电影数据。"""
    data = pd.read_csv(  # 读取 CSV 文件
        csv_path,  # 数据文件路径
        usecols=["电影名", "年份", "上映时间", "类型", "时长", "评分", "语言"],  # 只读取需要的列
        dtype={"年份": "Int64"},  # 设置年份列为可容纳缺失值的整数类型
    )
    data["年份"] = data["年份"].fillna(data["上映时间"].str[:4])  # 用上映时间前 4 位补齐缺失的年份
    return data  # 返回清洗后的数据表


def plot_year_distribution(data: pd.DataFrame, ax: Axes) -> Axes:
    """绘制每一年上映电影数量折线图。"""
    year_count = data.groupby("年份")["电影名"].count()  # 按年份统计电影数量
    min_year = int(year_count.index.min())  # 获取最小年份
    max_year = int(year_count.index.max())  # 获取最大年份
    x = list(range(min_year, max_year + 1))  # 生成完整年份列表
    y = [int(year_count.get(i, 0)) for i in x]  # 生成每一年对应的电影数量，缺失年份补 0

    ax.plot(x, y, color="green")  # 绘制折线图，颜色设为绿色
    ax.set_title("每一年上映的电影数量", fontsize=18)  # 设置子图标题
    ax.set_xlabel("年份", fontsize=14)  # 设置 x 轴标签
    ax.set_ylabel("电影数量", fontsize=14)  # 设置 y 轴标签
    ax.set_xticks(x[::10])  # 每隔 10 年显示一个刻度
    ax.set_yticks(list(range(0, 31, 3)))  # 设置 y 轴刻度范围为 0 到 30，间隔 3
    ax.grid(linestyle="--", alpha=0.5)  # 添加虚线网格，增强可读性
    return ax  # 返回当前坐标轴对象


def plot_language_distribution(data: pd.DataFrame, ax: Axes) -> Axes:
    """绘制不同语言电影数量柱状图。"""
    lang_count = data.groupby("语言")["语言"].count().sort_values(ascending=False)  # 按语言统计数量并降序排列

    ax.bar(lang_count.index, lang_count.values, color="green")  # 绘制柱状图
    ax.set_title("不同语言的电影数量", fontsize=18)  # 设置标题
    ax.set_xlabel("语言", fontsize=14)  # 设置 x 轴标签
    ax.set_ylabel("电影数量", fontsize=14)  # 设置 y 轴标签
    ax.grid(linestyle="--", alpha=0.5)  # 添加网格线
    ax.tick_params(axis="x", rotation=90)  # 旋转 x 轴刻度标签，方便查看
    return ax  # 返回当前坐标轴对象


def plot_type_distribution(data: pd.DataFrame, ax: Axes) -> Axes:
    """绘制不同类型电影数量柱状图。"""
    type_count = {}  # 创建空字典，用来统计每种类型出现次数
    for types in data["类型"].fillna("").str.split(","):  # 将类型字段按逗号分割
        for t in types:  # 遍历每个类型
            t = t.strip()  # 去掉空格
            if not t:  # 如果是空字符串，就跳过
                continue
            type_count[t] = type_count.get(t, 0) + 1  # 统计每种类型的数量

    x_types = list(type_count.keys())  # 取出类型名列表
    y_values = list(type_count.values())  # 取出对应数量列表

    ax.bar(x_types, y_values, color="green")  # 绘制柱状图
    ax.set_title("不同类型的电影数量", fontsize=18)  # 设置标题
    ax.set_xlabel("类型", fontsize=14)  # 设置 x 轴标签
    ax.set_ylabel("电影数量", fontsize=14)  # 设置 y 轴标签
    ax.grid(linestyle="--", alpha=0.5)  # 添加网格线
    ax.tick_params(axis="x", rotation=90)  # 旋转 x 轴标签，避免重叠
    return ax  # 返回当前坐标轴对象


def plot_score_distribution(data: pd.DataFrame, ax: Axes) -> Axes:
    """绘制不同评分电影数量饼图。"""
    score_count = data.groupby("评分")["评分"].count()  # 按评分统计电影数量
    total = score_count.sum()  # 统计所有评分对应电影数总和
    if total == 0:  # 如果没有数据，就报错
        raise ValueError("评分数据为空，无法绘制饼图。")

    large_scores = score_count.loc[score_count >= total * 0.02]  # 选出占比不小于 2% 的评分
    small_scores = score_count.loc[score_count < total * 0.02]  # 其余评分归为小类

    if not small_scores.empty:  # 如果有小类别，就把它们合并为“其他”
        large_scores = large_scores.copy()  # 复制一份，避免修改原数据
        large_scores["其他"] = small_scores.sum()  # 将小类别总数合并为“其他”

    scores = large_scores.index  # 取出评分标签
    scores_values = large_scores.values  # 取出对应数量

    ax.pie(scores_values, labels=scores, autopct="%1.1f%%", startangle=0)  # 绘制饼图，并显示占比
    ax.set_title("不同评分的电影数量", fontsize=18)  # 设置标题
    ax.legend(loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.3), fontsize=14)  # 设置图例位置
    ax.set_xlabel("评分", fontsize=14)  # 设置 x 轴标签
    ax.set_ylabel("电影数量", fontsize=14)  # 设置 y 轴标签
    ax.grid(linestyle="--", alpha=0.5)  # 给饼图加网格样式，保持整体风格一致
    ax.tick_params(axis="x", rotation=90)  # 旋转 x 轴刻度标签
    return ax  # 返回当前坐标轴对象


def draw_dashboard(data: pd.DataFrame, output_path: Path | None = None) -> None:
    """绘制完整的电影榜单分析图表。"""
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))  # 创建 2 行 2 列的子图布局
    fig.suptitle("TMDB-TOP300电影榜单分析", fontsize=23, x=0.5, y=0.98)  # 设置总标题
    fig.subplots_adjust(wspace=0.2, hspace=0.4)  # 调整子图之间的间距

    plot_year_distribution(data, axes[0, 0])  # 在左上子图绘制年份分布
    plot_language_distribution(data, axes[0, 1])  # 在右上子图绘制语言分布
    plot_type_distribution(data, axes[1, 0])  # 在左下子图绘制类型分布
    plot_score_distribution(data, axes[1, 1])  # 在右下子图绘制评分分布

    if output_path is not None:  # 如果指定了输出路径，就保存图片
        output_path.parent.mkdir(parents=True, exist_ok=True)  # 创建输出目录
        fig.tight_layout()  # 自动调整子图布局，避免重叠
        fig.savefig(output_path, dpi=300, bbox_inches="tight")  # 保存高清图片
        print(f"图表已保存到：{output_path}")  # 输出保存路径

    plt.close(fig)  # 关闭图片对象，释放资源


def main() -> None:
    """主函数。"""
    csv_path = find_data_file()  # 查找数据文件路径
    print(f"正在读取数据文件：{csv_path}")  # 输出正在读取的文件路径

    data = load_movie_data(csv_path)  # 读取并处理数据
    output_path = Path(__file__).resolve().parent / "010.TMDB-TOP300电影榜单分析.png"  # 设置输出图片路径
    draw_dashboard(data, output_path)  # 调用主绘图函数


if __name__ == "__main__":
    main()  # 运行主函数
