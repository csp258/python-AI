# AI时代技术人才招聘市场洞察系统 - 主程序入口
# 启动方式：
#   python main.py --gui             启动 tkinter 桌面应用（默认）
#   python main.py --web             启动 Streamlit Web 应用
#   python main.py --web --mock      强制使用模拟数据启动 Web 应用
#   python main.py --gui --mock      强制使用模拟数据启动桌面应用
#
# 【求职用途】
# 本系统可直接作为以下岗位的作品集项目：
# - 数据分析师（数据爬取→清洗→可视化 完整链路）
# - Python开发工程师（GUI + 多线程 + 数据库 + Web应用）
# - 数据工程师（ETL Pipeline + SQL + 数据处理）
# - AI产品经理（对AI岗位市场的深度洞察）

import sys
import os
import argparse

# 将项目根目录加入 Python 路径 —— 确保模块导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """检查依赖并返回缺失列表"""
    missing = []
    deps = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("requests", "requests"),
        ("bs4", "beautifulsoup4"),
        ("wordcloud", "wordcloud"),
        ("scipy", "scipy"),
        ("playwright", "playwright"),
    ]
    for module, pkg_name in deps:
        try:
            __import__(module)
        except ImportError:
            missing.append(pkg_name)
    return missing


def check_web_deps():
    """检查 Web 模式额外依赖"""
    missing = []
    for module, pkg_name in [("streamlit", "streamlit"), ("plotly", "plotly")]:
        try:
            __import__(module)
        except ImportError:
            missing.append(pkg_name)
    return missing


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI时代技术人才招聘市场洞察系统 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                   启动 tkinter 桌面应用（默认）
  python main.py --web             启动 Streamlit Web 应用
  python main.py --web --mock      使用模拟数据启动 Web 应用
  python main.py --gui --mock      使用模拟数据启动桌面应用

Web 应用启动后访问 http://localhost:8501
        """,
    )
    parser.add_argument(
        "--web", action="store_true",
        help="启动 Streamlit Web 应用（默认启动 tkinter GUI）"
    )
    parser.add_argument(
        "--gui", action="store_true",
        help="启动 tkinter 桌面应用"
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="强制使用模拟数据，跳过真实爬取"
    )
    args = parser.parse_args()

    # 默认模式：没有指定 --web 时走 GUI
    if not args.web and not args.gui:
        args.gui = True

    print("""
    ========================================================
       AI时代技术人才招聘市场洞察系统 v2.0
       AI-Era Tech Talent Market Insight System

       专业：数据科学与大数据技术
       技术栈：Python + SQLite + tkinter + matplotlib + Streamlit
       功能：爬取->清洗->存储->可视化->GUI/Web 双界面
    ========================================================
    """)

    # 检查核心依赖
    missing = check_dependencies()
    if missing:
        print(f"\n[警告] 缺少以下依赖包: {', '.join(missing)}")
        print(f"请运行: pip install -r requirements.txt\n")
        choice = input("是否继续启动？（缺少依赖可能导致部分功能不可用）[y/N]: ")
        if choice.lower() not in ("y", "yes"):
            sys.exit(1)

    if args.web:
        # ---- Streamlit Web 模式 ----
        web_missing = check_web_deps()
        if web_missing:
            print(f"\n[错误] Web 模式缺少依赖: {', '.join(web_missing)}")
            print(f"请运行: pip install {' '.join(web_missing)}")
            sys.exit(1)

        # 设置 mock 模式标志
        if args.mock:
            os.environ["AI_USE_MOCK"] = "1"

        print("[模式] Streamlit Web 应用")
        print("[启动] 正在启动 Web 服务器...")
        print("[访问] 打开浏览器访问 http://localhost:8501\n")

        import subprocess
        web_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_app.py")
        subprocess.run([sys.executable, "-m", "streamlit", "run", web_app_path])

    else:
        # ---- tkinter GUI 模式 ----
        if args.mock:
            os.environ["AI_USE_MOCK"] = "1"
            print("[模式] tkinter 桌面应用 (模拟数据)")

        from modules.gui import launch
        launch()
