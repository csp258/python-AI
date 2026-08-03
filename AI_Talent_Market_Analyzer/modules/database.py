# =============================================================================
# 数据存储模块 - SQLite 数据库操作封装
# =============================================================================
# 设计思想：使用 DAO（Data Access Object）模式，将对数据库的所有操作
# 封装在一个类中。这样做的好处：
# 1. 业务代码不直接写 SQL，降低耦合
# 2. 如果将来换成 MySQL/PostgreSQL，只改这一个文件即可
# 3. 面试时提到"DAO 模式 + 上下文管理器"是加分项

import sqlite3
import pandas as pd
from contextlib import contextmanager
from config import DB_PATH
import os


class Database:
    """
    数据库操作类 —— 封装所有 SQLite 操作的增删改查。

    SQLite 特点：
    - 轻量级：不需要安装数据库服务，数据存为单个 .db 文件
    - 跨平台：Windows/Mac/Linux 通吃
    - 适合：单机数据分析、个人项目、原型开发
    - 不适合：高并发 Web 应用（此时应选 PostgreSQL）
    """

    def __init__(self, db_path=None):
        """
        初始化数据库连接

        参数:
            db_path: 数据库文件路径，默认使用 config.DB_PATH
        """
        self.db_path = db_path or DB_PATH
        # 确保 data 目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # 启动时自动建表
        self._create_tables()

    # -------------------------------------------------------------------------
    # 上下文管理器 —— Python 的 with 语句支持
    # 使用 with self.get_conn() as conn: 可以自动管理连接和事务
    # 如果操作成功自动 commit，发生异常自动 rollback
    # -------------------------------------------------------------------------
    @contextmanager
    def get_conn(self):
        """获取数据库连接的上下文管理器 —— 自动处理提交与回滚"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 让查询结果可以用列名访问
        try:
            yield conn
            conn.commit()               # 一切正常 → 提交事务
        except Exception as e:
            conn.rollback()             # 发生异常 → 回滚事务
            raise e
        finally:
            conn.close()                # 无论如何 → 关闭连接

    # -------------------------------------------------------------------------
    # 建表语句
    # -------------------------------------------------------------------------
    def _create_tables(self):
        """
        创建数据表（如果不存在的话）。

        表结构设计说明：
        - id: 自增主键，每条记录的唯一标识
        - job_title: 职位名称，如 "Python开发工程师"
        - company_name: 公司名称
        - salary_min / salary_max: 薪资上下限（单位：千/月），分开存储方便计算
        - salary_avg: 平均薪资，预处理计算好，查询更快
        - city: 工作城市
        - district: 区/县
        - experience: 经验要求，如 "1-3年"
        - education: 学历要求，如 "本科"
        - company_size: 公司规模
        - company_type: 公司类型（民营/外企/国企等）
        - industry: 所属行业
        - skills: 技能标签，JSON 字符串存储
        - benefits: 福利待遇
        - post_date: 发布日期
        - job_url: 职位详情链接
        - source: 数据来源标记
        - created_at: 入库时间
        """
        create_sql = """
        CREATE TABLE IF NOT EXISTS job_listings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title       TEXT    NOT NULL,        -- 职位名称
            company_name    TEXT    NOT NULL,        -- 公司名称
            salary_min      REAL    DEFAULT 0,       -- 最低薪资(K/月)
            salary_max      REAL    DEFAULT 0,       -- 最高薪资(K/月)
            salary_avg      REAL    DEFAULT 0,       -- 平均薪资(K/月)
            city            TEXT    DEFAULT '未知',  -- 工作城市
            district        TEXT    DEFAULT '',       -- 区/县
            experience      TEXT    DEFAULT '不限',  -- 经验要求
            education       TEXT    DEFAULT '不限',  -- 学历要求
            company_size    TEXT    DEFAULT '未知',  -- 公司规模
            company_type    TEXT    DEFAULT '未知',  -- 公司类型
            industry        TEXT    DEFAULT '未知',  -- 所属行业
            skills          TEXT    DEFAULT '',       -- 技能标签(JSON)
            benefits        TEXT    DEFAULT '',       -- 福利待遇
            post_date       TEXT    DEFAULT '',       -- 发布日期
            job_url         TEXT    DEFAULT '',       -- 详情链接
            source          TEXT    DEFAULT '51job',  -- 数据来源
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 入库时间
        );

        -- 索引设计：加速常见查询
        CREATE INDEX IF NOT EXISTS idx_city    ON job_listings(city);
        CREATE INDEX IF NOT EXISTS idx_salary  ON job_listings(salary_avg);
        CREATE INDEX IF NOT EXISTS idx_title   ON job_listings(job_title);
        CREATE INDEX IF NOT EXISTS idx_edu     ON job_listings(education);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_job_url
            ON job_listings(job_url) WHERE job_url != '';
        """
        with self.get_conn() as conn:
            conn.executescript(create_sql)

    # -------------------------------------------------------------------------
    # 增：批量插入招聘数据
    # -------------------------------------------------------------------------
    def insert_jobs(self, jobs: list[dict]) -> int:
        """
        批量插入职位数据 —— 使用 executemany 提高性能

        参数:
            jobs: 字典列表，每个字典代表一条职位记录

        返回:
            实际插入的记录条数

        设计要点：
        - INSERT OR IGNORE：按 job_url 去重，避免重复采集同一条数据
        - 先创建唯一索引再插入，利用数据库层面的去重能力
        """
        if not jobs:
            return 0

        insert_sql = """
        INSERT OR IGNORE INTO job_listings
            (job_title, company_name, salary_min, salary_max, salary_avg,
             city, district, experience, education, company_size,
             company_type, industry, skills, benefits, post_date, job_url, source)
        VALUES
            (:job_title, :company_name, :salary_min, :salary_max, :salary_avg,
             :city, :district, :experience, :education, :company_size,
             :company_type, :industry, :skills, :benefits, :post_date, :job_url, :source)
        """
        with self.get_conn() as conn:
            cursor = conn.executemany(insert_sql, jobs)
            return cursor.rowcount

    # -------------------------------------------------------------------------
    # 删：清空表数据（用于重新采集）
    # -------------------------------------------------------------------------
    def clear_all(self) -> int:
        """清空职位表，返回被删除的记录数"""
        with self.get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM job_listings").fetchone()[0]
            conn.execute("DELETE FROM job_listings")
            return count

    # -------------------------------------------------------------------------
    # 查：统计信息
    # -------------------------------------------------------------------------
    def get_count(self) -> int:
        """获取当前数据库中的职位总数"""
        with self.get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM job_listings").fetchone()
            return row[0]

    def get_stats(self) -> dict:
        """
        获取数据库概览统计 —— 用于在 GUI 首页展示

        返回包含以下统计指标的字典：
        - total_jobs: 总职位数
        - total_companies: 公司数量
        - avg_salary: 整体平均薪资
        - cities: 覆盖城市数
        - date_range: 数据时间范围
        """
        with self.get_conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM job_listings"
            ).fetchone()[0]

            companies = conn.execute(
                "SELECT COUNT(DISTINCT company_name) FROM job_listings"
            ).fetchone()[0]

            avg_sal = conn.execute(
                "SELECT AVG(salary_avg) FROM job_listings WHERE salary_avg > 0"
            ).fetchone()[0] or 0

            cities = conn.execute(
                "SELECT COUNT(DISTINCT city) FROM job_listings WHERE city != '未知'"
            ).fetchone()[0]

            return {
                "total_jobs": total,
                "total_companies": companies,
                "avg_salary": round(avg_sal, 2),
                "cities": cities,
            }

    # -------------------------------------------------------------------------
    # 查：获取 DataFrame —— 数据分析的核心入口
    # -------------------------------------------------------------------------
    def to_dataframe(self, query=None) -> pd.DataFrame:
        """
        将数据库内容导出为 pandas DataFrame

        参数:
            query: 自定义 SQL 查询（可选），默认查询全表

        返回:
            pandas DataFrame，方便后续数据分析和可视化

        这是整个系统最核心的数据流通方式：
        数据库 → DataFrame → 数据处理/可视化
        """
        if query is None:
            query = "SELECT * FROM job_listings"

        with self.get_conn() as conn:
            df = pd.read_sql_query(query, conn)
        return df

    # -------------------------------------------------------------------------
    # 查：分析查询方法 —— 直接返回聚合结果
    # -------------------------------------------------------------------------
    def get_city_distribution(self) -> pd.DataFrame:
        """城市岗位分布 Top15"""
        query = """
        SELECT city, COUNT(*) as count, ROUND(AVG(salary_avg), 2) as avg_salary
        FROM job_listings
        WHERE city != '未知'
        GROUP BY city
        ORDER BY count DESC
        LIMIT 15
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_education_distribution(self) -> pd.DataFrame:
        """学历要求分布"""
        query = """
        SELECT education, COUNT(*) as count
        FROM job_listings
        WHERE education != '不限'
        GROUP BY education
        ORDER BY count DESC
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_experience_distribution(self) -> pd.DataFrame:
        """经验要求分布"""
        query = """
        SELECT experience, COUNT(*) as count, ROUND(AVG(salary_avg), 2) as avg_salary
        FROM job_listings
        WHERE experience != '不限'
        GROUP BY experience
        ORDER BY
            CASE experience
                WHEN '在校生/应届生' THEN 1
                WHEN '无需经验' THEN 1
                WHEN '1年经验' THEN 2
                WHEN '2年经验' THEN 3
                WHEN '3-4年经验' THEN 4
                WHEN '3年及以上' THEN 4
                WHEN '5-7年经验' THEN 5
                WHEN '8-9年经验' THEN 6
                WHEN '10年以上经验' THEN 7
                ELSE 8
            END
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_industry_distribution(self) -> pd.DataFrame:
        """行业分布 Top15"""
        query = """
        SELECT industry, COUNT(*) as count, ROUND(AVG(salary_avg), 2) as avg_salary
        FROM job_listings
        WHERE industry != '未知'
        GROUP BY industry
        ORDER BY count DESC
        LIMIT 15
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_salary_by_city(self) -> pd.DataFrame:
        """各城市薪资对比（岗位数>=5的城市）"""
        query = """
        SELECT city,
               COUNT(*) as count,
               ROUND(AVG(salary_avg), 2) as avg_salary,
               ROUND(MIN(salary_min), 2) as min_salary,
               ROUND(MAX(salary_max), 2) as max_salary
        FROM job_listings
        WHERE city != '未知' AND salary_avg > 0
        GROUP BY city
        HAVING count >= 3
        ORDER BY avg_salary DESC
        LIMIT 20
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_salary_by_education(self) -> pd.DataFrame:
        """学历-薪资关系"""
        query = """
        SELECT education,
               COUNT(*) as count,
               ROUND(AVG(salary_avg), 2) as avg_salary,
               ROUND(MIN(salary_avg), 2) as min_salary,
               ROUND(MAX(salary_avg), 2) as max_salary
        FROM job_listings
        WHERE education != '不限' AND salary_avg > 0
        GROUP BY education
        ORDER BY avg_salary DESC
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_company_size_distribution(self) -> pd.DataFrame:
        """公司规模分布"""
        query = """
        SELECT company_size, COUNT(*) as count, ROUND(AVG(salary_avg), 2) as avg_salary
        FROM job_listings
        WHERE company_size != '未知'
        GROUP BY company_size
        ORDER BY count DESC
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_title_keywords(self) -> pd.DataFrame:
        """职位高频关键词"""
        query = """
        SELECT job_title, COUNT(*) as count
        FROM job_listings
        GROUP BY job_title
        ORDER BY count DESC
        LIMIT 30
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)

    def get_daily_trend(self) -> pd.DataFrame:
        """每日发布趋势"""
        query = """
        SELECT post_date, COUNT(*) as count
        FROM job_listings
        WHERE post_date != ''
        GROUP BY post_date
        ORDER BY post_date
        """
        with self.get_conn() as conn:
            return pd.read_sql_query(query, conn)
