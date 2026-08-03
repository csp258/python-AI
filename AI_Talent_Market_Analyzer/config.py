# =============================================================================
# AI时代技术人才招聘市场洞察系统 - 全局配置文件
# =============================================================================
# 本文件集中管理项目的所有配置参数，修改配置时只需改动此文件。
# 这种设计遵循"配置与代码分离"原则，在求职面试中提及可加分。

import os

# ----------------------------- 项目根路径 -----------------------------
# os.path.dirname(__file__)：获取当前文件(config.py)所在目录
# os.path.abspath()：转为绝对路径，确保任意位置启动都正确
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ----------------------------- 数据库配置 -----------------------------
# 使用 SQLite 存储数据 —— 零配置、跨平台、适合单机分析系统
DB_PATH = os.path.join(BASE_DIR, "data", "jobs.db")

# ----------------------------- 数据爬取配置 -----------------------------
# 请求头 —— 模拟正常浏览器访问，避免被反爬虫拦截
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# 爬取控制参数
MAX_PAGES = 15                  # 最大爬取页数（每页约50条，15页 ≈ 750条 > 300条要求）
REQUEST_DELAY = 2.0             # 请求间隔秒数 —— 避免对目标服务器造成压力
REQUEST_TIMEOUT = 15            # 单次请求超时秒数
MAX_RETRIES = 3                 # 请求失败最大重试次数

# ----------------------------- 目标搜索关键词 -----------------------------
# AI/大数据/开发 方向的职位关键词 —— 紧扣"紧跟时代"主题
SEARCH_KEYWORDS = [
    "Python开发", "数据分析", "大数据", "人工智能",
    "机器学习", "深度学习", "NLP", "计算机视觉",
    "数据挖掘", "后端开发"
]

# ----------------------------- 数据清洗配置 -----------------------------
# 停用词列表 —— 用于技能关键词提取时过滤无意义词汇
STOP_WORDS = {
    "熟练", "熟悉", "了解", "掌握", "具有", "以上", "相关",
    "经验", "优先", "能力", "工作", "要求", "任职", "岗位",
    "职责", "负责", "进行", "以及", "其他", "公司", "团队",
    "the", "a", "an", "and", "or", "in", "of", "to", "for",
    "with", "on", "at", "by", "from", "is", "are", "be"
}

# ----------------------------- GUI 界面配置 -----------------------------
# 主窗口设置
WINDOW_TITLE = "AI时代技术人才招聘市场洞察系统 v2.0"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# 颜色主题 —— 深色专业风格（参考 VS Code 暗色主题）
COLORS = {
    "bg_dark": "#1e1e2e",        # 主背景色
    "bg_medium": "#2d2d44",      # 次级背景色
    "bg_light": "#3a3a5c",       # 面板背景色
    "accent": "#7c3aed",         # 主强调色（紫色，AI感）
    "accent_hover": "#9061f9",   # 悬停强调色
    "text_primary": "#e0e0f0",   # 主文字色
    "text_secondary": "#a0a0c0", # 次级文字色
    "success": "#10b981",        # 成功/绿色
    "warning": "#f59e0b",        # 警告/橙色
    "danger": "#ef4444",         # 错误/红色
    "chart_colors": [            # 图表配色（10色系）
        "#7c3aed", "#06b6d4", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#3b82f6", "#14b8a6", "#e11d48"
    ]
}

# ----------------------------- 字体配置 -----------------------------
# 中文字体 —— 跨平台适配
import platform
_system = platform.system()
if _system == "Windows":
    FONT_FAMILY = "Microsoft YaHei"
elif _system == "Darwin":       # macOS
    FONT_FAMILY = "PingFang SC"
else:                           # Linux
    FONT_FAMILY = "WenQuanYi Micro Hei"

# matplotlib 全局字体设置
import matplotlib
matplotlib.rcParams["font.sans-serif"] = [FONT_FAMILY, "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
