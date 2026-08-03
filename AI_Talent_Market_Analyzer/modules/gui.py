# =============================================================================
# 图形用户界面模块 - tkinter 构建的专业数据分析桌面应用
# =============================================================================
# 设计思想：
# 1. 采用 "MVC 模式"：View(本模块) 通过回调与 Controller(main.py) 通信
# 2. 左侧导航栏 + 右侧内容区 的经典"后台管理系统"布局
# 3. matplotlib Figure 通过 FigureCanvasTkAgg 嵌入 tkinter
# 4. 暗色专业主题 —— 模拟 VS Code / PyCharm 风格
#
# 【求职加分点】
# - tkinter 虽"老"但实用：Python 标准库，零依赖部署
# - 自定义组件封装：CustomButton、ChartPanel 等
# - 线程安全：数据操作在后台线程，UI 通过 after() 轮询更新

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from config import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, COLORS, FONT_FAMILY
)
from modules.database import Database
from modules.data_processor import DataProcessor
from modules.visualization import JobVisualizer
from modules.crawler import fetch_jobs, MockDataGenerator
from modules.report_generator import generate_report


# 提取配色
C = COLORS


# =========================================================================
# 自定义组件：圆角按钮（模拟）
# =========================================================================
class ModernButton(tk.Canvas):
    """
    自定义现代风格按钮

    为什么不用 ttk.Button？
    - ttk 样式自定义受限（尤其在暗色主题下）
    - Canvas 可以完全控制每个像素
    - 展示"深入理解 tkinter 底层"的能力
    """

    def __init__(self, parent, text, command=None, width=160, height=38,
                 bg=C["accent"], hover_bg=C["accent_hover"], fg="white",
                 font_size=11, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=C["bg_dark"], highlightthickness=0, **kwargs)

        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.text = text
        self.font = (FONT_FAMILY, font_size)
        self._hovered = False

        # 绘制按钮
        self._draw()

        # 绑定事件
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        """绘制按钮"""
        self.delete("all")
        color = self.hover_bg if self._hovered else self.bg
        # 圆角矩形（用弧线模拟）
        r = 8
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=color, outline="")
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=color, outline="")
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=color, outline="")
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=color, outline="")
        self.create_rectangle(r, 0, w-r, h, fill=color, outline="")
        self.create_rectangle(0, r, w, h-r, fill=color, outline="")
        # 文字
        self.create_text(w/2, h/2, text=self.text, fill=self.fg,
                         font=self.font, anchor="center")

    def _on_enter(self, event):
        self._hovered = True
        self._draw()

    def _on_leave(self, event):
        self._hovered = False
        self._draw()

    def _on_click(self, event):
        if self.command:
            self.command()


# =========================================================================
# 图表画布面板 —— 封装 matplotlib Figure 到 tkinter
# =========================================================================
class ChartPanel(ttk.Frame):
    """
    图表显示面板 —— 将 matplotlib 图表嵌入 tkinter Frame

    工作流程：
    1. 外部调用 display_chart(fig) 传入 matplotlib Figure
    2. 自动清除旧图表，绘制新图表
    3. 包含 NavigationToolbar（缩放、平移、保存等功能）

    面试时提到 "matplotlib + tkinter 混合编程" 说明你有
    桌面应用开发经验，这在数据分析岗位是稀缺技能。
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style="Chart.TFrame")

        # 控制栏
        self.toolbar_frame = ttk.Frame(self)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        # 标题标签
        self.title_label = ttk.Label(
            self.toolbar_frame,
            text="请选择左侧图表开始分析",
            font=(FONT_FAMILY, 14, "bold"),
            foreground=C["text_primary"],
            background=C["bg_medium"],
        )
        self.title_label.pack(side=tk.LEFT, padx=15, pady=8)

        # 画布容器
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.canvas = None
        self.toolbar = None
        self.current_fig = None

    def display_chart(self, fig: Figure, title: str = ""):
        """
        显示图表

        参数:
            fig: matplotlib Figure 对象
            title: 当前图表标题
        """
        # 清除旧内容
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        if title:
            self.title_label.configure(text=title)

        self.current_fig = fig

        # 创建 Canvas
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加工具栏
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.RIGHT, padx=5)

    def clear(self):
        """清除当前图表"""
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        self.title_label.configure(text="请选择左侧图表开始分析")
        self.current_fig = None


# =========================================================================
# 左侧导航栏
# =========================================================================
class Sidebar(ttk.Frame):
    """
    左侧图表导航栏

    设计：
    - 滚动区域包含所有图表按钮
    - 分类分组（分布类、对比类、关系类、综合类）
    - 点击按钮 → 回调主窗口切换图表
    """

    def __init__(self, parent, chart_callback, **kwargs):
        """
        参数:
            chart_callback: 图表切换回调函数 func(chart_key)
        """
        super().__init__(parent, **kwargs)
        self.configure(style="Sidebar.TFrame")
        self.chart_callback = chart_callback

        # 标题
        title = ttk.Label(
            self, text="📊 图表导航",
            font=(FONT_FAMILY, 14, "bold"),
            foreground=C["text_primary"],
            background=C["bg_dark"],
        )
        title.pack(pady=(15, 10))

        # 可滚动画布
        canvas = tk.Canvas(self, bg=C["bg_dark"], highlightthickness=0,
                           width=240)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas, style="Sidebar.TFrame")

        self.scroll_frame.bind("<Configure>",
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw",
                             width=225)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮滚动
        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        # 图表分类和按钮
        self._create_chart_sections()

    def _create_chart_sections(self):
        """创建分类图表按钮组"""
        sections = {
            "📈 分布与构成": [
                "1-城市岗位分布", "3-学历要求饼图", "7-公司规模环形图",
                "17-薪资区间环形图", "19-资历等级分布", "21-岗位类型分布",
            ],
            "💰 薪资分析": [
                "2-薪资分布直方图", "4-经验要求与薪资", "8-薪资箱线图",
                "10-城市薪资对比", "12-学历薪资箱线图", "15-薪资气泡图",
                "20-公司规模薪资", "22-学历经验交叉热力图",
            ],
            "🔍 行业与技能": [
                "5-行业需求排行", "6-技能词云", "11-热门技能排行",
                "13-行业薪资雷达图", "18-技能共现热力图",
            ],
            "🤖 AI专项分析": [
                "14-AI vs 非AI对比", "9-岗位发布趋势", "16-公司类型薪资",
                "23-福利词云",
            ],
            "📋 综合视图": [
                "仪表盘-全景总览",
            ],
        }

        for section_name, charts in sections.items():
            # 分类标题
            sec_label = ttk.Label(
                self.scroll_frame, text=section_name,
                font=(FONT_FAMILY, 11, "bold"),
                foreground=C["accent"],
                background=C["bg_dark"],
            )
            sec_label.pack(anchor="w", padx=15, pady=(12, 5))

            # 图表按钮
            for chart_key in charts:
                btn = tk.Button(
                    self.scroll_frame,
                    text=f"  {chart_key.split('-', 1)[-1]}",
                    font=(FONT_FAMILY, 10),
                    bg=C["bg_light"],
                    fg=C["text_primary"],
                    activebackground=C["accent"],
                    activeforeground="white",
                    relief=tk.FLAT,
                    cursor="hand2",
                    anchor="w",
                    padx=15, pady=6,
                    bd=0,
                    command=lambda k=chart_key: self.chart_callback(k),
                )
                btn.pack(fill=tk.X, padx=10, pady=1)

                # 悬停效果
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=C["accent"]))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=C["bg_light"]))


# =========================================================================
# 顶部工具栏
# =========================================================================
class Toolbar(ttk.Frame):
    """顶部操作工具栏"""

    def __init__(self, parent, callbacks: dict, **kwargs):
        """
        参数:
            callbacks: {"action_name": callback_function} 字典
        """
        super().__init__(parent, **kwargs)
        self.configure(style="Toolbar.TFrame")

        # 应用标题
        title = ttk.Label(
            self, text="AI时代技术人才招聘市场洞察系统",
            font=(FONT_FAMILY, 16, "bold"),
            foreground=C["text_primary"],
            background=C["bg_medium"],
        )
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # 右侧按钮组
        btn_frame = ttk.Frame(self, style="Toolbar.TFrame")
        btn_frame.pack(side=tk.RIGHT, padx=15, pady=8)

        button_configs = [
            ("🔄 刷新数据", "refresh", C["accent"]),
            ("📥 导出报告", "export", C["success"]),
            ("📊 数据统计", "stats", C["accent"]),
            ("❓ 使用帮助", "help", "#6b7280"),
        ]

        for text, action, color in button_configs:
            btn = tk.Button(
                btn_frame, text=text,
                font=(FONT_FAMILY, 10),
                bg=color, fg="white",
                activebackground=C["accent_hover"],
                activeforeground="white",
                relief=tk.FLAT,
                cursor="hand2",
                padx=15, pady=5,
                bd=0,
                command=callbacks.get(action),
            )
            btn.pack(side=tk.LEFT, padx=3)

            # 悬停效果
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.configure(bg=C["accent_hover"]))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=color))


# =========================================================================
# 底部状态栏
# =========================================================================
class StatusBar(ttk.Frame):
    """底部状态栏 —— 显示数据概览和状态信息"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style="Status.TFrame")

        self.status_label = ttk.Label(
            self, text="就绪",
            font=(FONT_FAMILY, 9),
            foreground=C["text_secondary"],
            background=C["bg_medium"],
        )
        self.status_label.pack(side=tk.LEFT, padx=15, pady=5)

        self.stats_label = ttk.Label(
            self, text="",
            font=(FONT_FAMILY, 9),
            foreground=C["text_secondary"],
            background=C["bg_medium"],
        )
        self.stats_label.pack(side=tk.RIGHT, padx=15, pady=5)

        self.time_label = ttk.Label(
            self, text="",
            font=(FONT_FAMILY, 9),
            foreground=C["text_secondary"],
            background=C["bg_medium"],
        )
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def set_stats(self, text: str):
        self.stats_label.configure(text=text)

    def update_time(self):
        self.time_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.after(1000, self.update_time)


# =========================================================================
# 进度对话框
# =========================================================================
class ProgressDialog(tk.Toplevel):
    """数据加载进度对话框"""

    def __init__(self, parent, title="处理中..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x120")
        self.configure(bg=C["bg_medium"])
        self.resizable(False, False)
        self.transient(parent)

        # 居中显示
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 380) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 120) // 2
        self.geometry(f"+{x}+{y}")

        self.label = ttk.Label(
            self, text="正在处理数据，请稍候...",
            font=(FONT_FAMILY, 11),
            foreground=C["text_primary"],
            background=C["bg_medium"],
        )
        self.label.pack(pady=(20, 10))

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=300)
        self.progress.pack(pady=10)
        self.progress.start(15)

        # 让对话框置顶
        self.grab_set()
        self.focus_set()

    def set_text(self, text: str):
        self.label.configure(text=text)

    def close(self):
        self.progress.stop()
        self.grab_release()
        self.destroy()


# =========================================================================
# 主窗口
# =========================================================================
class MainWindow:
    """
    主应用程序窗口

    布局结构：
    ┌──────────────────────────────────────────┐
    │              Toolbar（顶部工具栏）          │
    ├────────┬─────────────────────────────────┤
    │ Sidebar│     ChartPanel（图表显示区）       │
    │ 导航栏  │                                  │
    │        │                                  │
    ├────────┴─────────────────────────────────┤
    │              StatusBar（底部状态栏）        │
    └──────────────────────────────────────────┘
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        # 让窗口在屏幕居中
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w - WINDOW_WIDTH) // 2
        y = (screen_h - WINDOW_HEIGHT) // 2
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.root.minsize(1000, 700)
        self.root.configure(bg=C["bg_dark"])

        # ---- 数据层 ----
        self.db = Database()
        self.df = None
        self.visualizer = None

        # ---- 配置 ttk 样式 ----
        self._setup_styles()

        # ---- 构建 UI ----
        self._build_ui()

        # ---- 加载数据 ----
        self._load_data()

        # ---- 更新时间 ----
        self.status_bar.update_time()

        # ---- 绑定关闭事件 ----
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -----------------------------------------------------------------
    # ttk 样式配置
    # -----------------------------------------------------------------
    def _setup_styles(self):
        """配置 ttk 组件样式（暗色主题）"""
        style = ttk.Style()

        style.configure("Toolbar.TFrame", background=C["bg_medium"])
        style.configure("Sidebar.TFrame", background=C["bg_dark"])
        style.configure("Status.TFrame", background=C["bg_medium"])
        style.configure("Chart.TFrame", background=C["bg_medium"])

        # 滚动条样式
        style.configure("Vertical.TScrollbar",
                        background=C["bg_light"],
                        troughcolor=C["bg_dark"],
                        arrowcolor=C["text_secondary"],
                        )

    # -----------------------------------------------------------------
    # 构建 UI 布局
    # -----------------------------------------------------------------
    def _build_ui(self):
        """构建界面布局"""
        # ---- 工具栏 ----
        self.toolbar = Toolbar(self.root, callbacks={
            "refresh": self._on_refresh,
            "export": self._on_export,
            "stats": self._on_show_stats,
            "help": self._on_help,
        })
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # ---- 主体区域 ----
        main_area = ttk.Frame(self.root)
        main_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 左侧导航栏
        self.sidebar = Sidebar(main_area, chart_callback=self._on_chart_select)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # 分隔线
        separator = tk.Frame(main_area, bg=C["bg_light"], width=2)
        separator.pack(side=tk.LEFT, fill=tk.Y)

        # 右侧图表区域
        self.chart_panel = ChartPanel(main_area)
        self.chart_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ---- 状态栏 ----
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # ---- 进度提示 ----
        self.progress_var = tk.StringVar(value="")

    # -----------------------------------------------------------------
    # 数据加载
    # -----------------------------------------------------------------
    def _load_data(self):
        """加载数据（优先从数据库，否则爬取/生成）"""
        count = self.db.get_count()

        if count >= 300:
            # 数据库已有数据，直接加载
            self._load_from_db()
        else:
            # 首次启动，爬取数据并入库
            self._fetch_and_load()

    def _load_from_db(self):
        """从数据库加载数据"""
        self.status_bar.set_status("正在从数据库加载数据...")

        def task():
            self.df = self.db.to_dataframe()
            self.df = DataProcessor().pipeline(self.df)
            self.visualizer = JobVisualizer(self.df)
            stats = self._compute_stats()

            # UI 更新必须在主线程
            self.root.after(0, lambda: self._on_data_ready(stats))

        threading.Thread(target=task, daemon=True).start()

    def _fetch_and_load(self):
        """爬取/生成数据并入库"""
        import os
        progress = ProgressDialog(self.root, "正在获取数据")

        def task():
            try:
                use_mock = os.environ.get("AI_USE_MOCK") == "1"
                if use_mock:
                    progress.set_text("正在生成演示数据...")
                    jobs = MockDataGenerator.generate(500)
                else:
                    progress.set_text("正在采集招聘数据...")
                    jobs = fetch_jobs(use_mock=False, max_pages=10)

                progress.set_text(f"已获取 {len(jobs)} 条，正在入库...")
                inserted = self.db.insert_jobs(jobs)
                print(f"入库 {inserted} 条记录")

                progress.set_text("正在处理和分析数据...")
                self.df = self.db.to_dataframe()
                self.df = DataProcessor().pipeline(self.df)
                self.visualizer = JobVisualizer(self.df)
                stats = self._compute_stats()

                self.root.after(0, lambda: self._on_data_ready(stats))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"数据加载失败: {e}"))
            finally:
                self.root.after(0, progress.close)

        threading.Thread(target=task, daemon=True).start()

    def _compute_stats(self) -> dict:
        """从处理后的 DataFrame 计算统计信息，而非查询原始数据库"""
        if self.df is None or self.df.empty:
            return {"total_jobs": 0, "avg_salary": 0, "cities": 0}
        df = self.df
        total = len(df)
        avg_sal = round(df.loc[df["salary_avg"] > 0, "salary_avg"].mean(), 1)
        cities = df.loc[df["city"] != "未知", "city"].nunique()
        companies = df.loc[df["company_name"] != "未知公司", "company_name"].nunique()
        return {
            "total_jobs": total,
            "total_companies": companies,
            "avg_salary": avg_sal,
            "cities": cities,
        }

    def _on_data_ready(self, stats: dict):
        """数据加载完成后的回调"""
        total = stats.get("total_jobs", 0)
        avg_sal = stats.get("avg_salary", 0)
        cities = stats.get("cities", 0)

        self.status_bar.set_stats(
            f"总岗位: {total} | 平均薪资: {avg_sal}K/月 | 覆盖城市: {cities}个"
        )
        self.status_bar.set_status("就绪 —— 请选择左侧图表开始分析")

        # 默认显示仪表盘
        self._show_chart("仪表盘-全景总览")

    # -----------------------------------------------------------------
    # 图表切换
    # -----------------------------------------------------------------
    def _on_chart_select(self, chart_key: str):
        """左侧导航栏点击回调"""
        self._show_chart(chart_key)

    def _show_chart(self, chart_key: str):
        """显示指定图表"""
        if self.visualizer is None:
            messagebox.showwarning("提示", "数据尚未加载完成，请稍候...")
            return

        # 获取图表名称和函数
        chart_name = chart_key.split("-", 1)[-1] if "-" in chart_key else chart_key

        all_charts = self.visualizer.get_all_charts()
        chart_func = all_charts.get(chart_key)

        if chart_func is None:
            messagebox.showwarning("提示", f"未知图表: {chart_key}")
            return

        self.status_bar.set_status(f"正在渲染: {chart_name}...")

        try:
            fig = chart_func()
            self.chart_panel.display_chart(fig, title=f"📊 {chart_name}")
            self.status_bar.set_status(f"当前图表: {chart_name}")
        except Exception as e:
            messagebox.showerror("图表渲染失败", f"渲染 {chart_name} 时出错:\n{e}")
            self.status_bar.set_status("渲染失败")

    # -----------------------------------------------------------------
    # 工具栏操作回调
    # -----------------------------------------------------------------
    def _on_refresh(self):
        """刷新数据"""
        if not messagebox.askyesno("确认刷新", "将重新获取数据并覆盖现有数据，是否继续？"):
            return

        self.db.clear_all()
        self.chart_panel.clear()
        self.status_bar.set_status("正在刷新数据...")
        self._fetch_and_load()

    def _on_export(self):
        """导出分析报告"""
        if self.df is None:
            messagebox.showwarning("提示", "没有可导出的数据")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出分析报告",
            defaultextension=".html",
            filetypes=[
                ("HTML 报告", "*.html"),
                ("Excel 文件", "*.xlsx"),
                ("CSV 文件", "*.csv"),
            ]
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".html"):
                self.status_bar.set_status("正在生成分析报告...")
                generate_report(self.df, self.visualizer, output_path=file_path)
                self.status_bar.set_status(f"报告已导出至: {file_path}")
                messagebox.showinfo("导出成功",
                    f"HTML 分析报告已生成:\n{file_path}\n\n用浏览器打开即可查看完整报告。")
            elif file_path.endswith(".csv"):
                self.df.to_csv(file_path, index=False, encoding="utf-8-sig")
                self.status_bar.set_status(f"数据已导出至: {file_path}")
                messagebox.showinfo("导出成功", f"数据已导出:\n{file_path}")
            else:
                self.df.to_excel(file_path, index=False, engine="openpyxl")
                self.status_bar.set_status(f"数据已导出至: {file_path}")
                messagebox.showinfo("导出成功", f"数据已导出:\n{file_path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _on_show_stats(self):
        """显示数据统计信息"""
        if self.df is None:
            messagebox.showwarning("提示", "数据尚未加载")
            return

        stats = self.db.get_stats()

        # 计算更多统计
        ai_count = 0
        if "is_ai_position" in self.df.columns:
            ai_count = (self.df["is_ai_position"] == "是").sum()

        info_text = f"""
╔══════════════════════════════════╗
║     招聘市场数据统计报告           ║
╠══════════════════════════════════╣
║  总职位数量:    {stats['total_jobs']:>6} 条             ║
║  公司数量:      {stats['total_companies']:>6} 家             ║
║  覆盖城市:      {stats['cities']:>6} 个             ║
║  平均薪资:      {stats['avg_salary']:>6.1f} K/月       ║
║  AI岗位数:      {ai_count:>6} 个             ║
╚══════════════════════════════════╝

数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据来源: 51job真实数据 + 智能补充
        """

        messagebox.showinfo("数据统计", info_text)

    def _on_help(self):
        """显示使用帮助"""
        help_text = """
🎯 AI时代技术人才招聘市场洞察系统 v2.0

【使用说明】
1. 左侧导航栏选择需要查看的图表类型
2. 图表支持缩放、平移、保存等操作（使用底部工具栏）
3. 点击「刷新数据」重新获取最新招聘数据
4. 点击「导出报告」将数据导出为 Excel/CSV 文件

【图表分类】
📈 分布与构成：了解岗位的地理、学历、规模分布
💰 薪资分析：多维度薪资对比与分析
🔍 行业与技能：洞察市场需求和技能趋势
🤖 AI专项分析：AI岗位 vs 传统岗位专项对比
📋 综合视图：多图合一全景仪表盘

【技术栈】
- 数据爬取: Playwright (真实浏览器自动化)
- 数据处理: pandas + numpy
- 数据存储: SQLite3
- GUI界面: tkinter (Python标准库)
- 可视化: matplotlib + wordcloud

【适用场景】
- 求职决策：了解目标城市/行业的薪资水平
- 技能规划：发现市场最需要的技术栈
- 行业研究：分析技术人才市场趋势
        """
        messagebox.showinfo("使用帮助", help_text)

    # -----------------------------------------------------------------
    # 关闭窗口
    # -----------------------------------------------------------------
    def _on_close(self):
        """程序退出处理"""
        if messagebox.askokcancel("退出确认", "确定要退出系统吗？"):
            self.root.destroy()


# =========================================================================
# 启动函数
# =========================================================================
def launch():
    """
    启动 GUI 应用程序

    这是整个项目的入口，被 main.py 调用。

    面试小贴士：
    把 main() 函数封装在 if __name__ == "__main__" 中，
    让模块可以被 import 而不自动运行 —— 这是一个好的编程习惯。
    """
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
