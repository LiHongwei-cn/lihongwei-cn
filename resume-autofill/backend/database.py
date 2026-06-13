"""数据库模型 — SQLite 本地存储"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "resume.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
    -- 个人信息主表
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY DEFAULT 1,
        -- 基本信息
        name TEXT NOT NULL DEFAULT '',
        gender TEXT DEFAULT '',
        birth_date TEXT DEFAULT '',
        ethnicity TEXT DEFAULT '',
        political_status TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        wechat TEXT DEFAULT '',
        qq TEXT DEFAULT '',
        -- 地址
        hometown TEXT DEFAULT '',
        current_city TEXT DEFAULT '',
        current_address TEXT DEFAULT '',
        -- 教育
        university TEXT DEFAULT '',
        college TEXT DEFAULT '',
        major TEXT DEFAULT '',
        degree TEXT DEFAULT '',
        enrollment_year TEXT DEFAULT '',
        graduation_year TEXT DEFAULT '',
        gpa TEXT DEFAULT '',
        ranking TEXT DEFAULT '',
        -- 求职意向
        target_position TEXT DEFAULT '',
        target_city TEXT DEFAULT '',
        expected_salary TEXT DEFAULT '',
        available_date TEXT DEFAULT '',
        -- 照片路径
        photo_path TEXT DEFAULT '',
        -- 自我评价
        self_intro TEXT DEFAULT '',
        -- JSON 数组字段
        skills TEXT DEFAULT '[]',
        languages TEXT DEFAULT '[]',
        hobbies TEXT DEFAULT '[]',
        -- 时间戳
        updated_at TEXT DEFAULT ''
    );

    -- 教育经历
    CREATE TABLE IF NOT EXISTS education (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school TEXT NOT NULL,
        college TEXT DEFAULT '',
        major TEXT DEFAULT '',
        degree TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        gpa TEXT DEFAULT '',
        ranking TEXT DEFAULT '',
        courses TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    );

    -- 项目经历
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT DEFAULT '',
        company TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        description TEXT DEFAULT '',
        achievements TEXT DEFAULT '',
        tech_stack TEXT DEFAULT '',
        url TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    );

    -- 工作/实习经历
    CREATE TABLE IF NOT EXISTS work_experience (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        position TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        description TEXT DEFAULT '',
        achievements TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    );

    -- 奖项荣誉
    CREATE TABLE IF NOT EXISTS awards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        level TEXT DEFAULT '',
        issuer TEXT DEFAULT '',
        date TEXT DEFAULT '',
        description TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    );

    -- 证书资质
    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        issuer TEXT DEFAULT '',
        date TEXT DEFAULT '',
        number TEXT DEFAULT '',
        expiry TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    );

    -- 社团/组织经历
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        description TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    );

    -- 发表论文/专利
    CREATE TABLE IF NOT EXISTS publications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        authors TEXT DEFAULT '',
        venue TEXT DEFAULT '',
        date TEXT DEFAULT '',
        doi TEXT DEFAULT '',
        type TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    );

    -- 志愿服务
    CREATE TABLE IF NOT EXISTS volunteer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization TEXT NOT NULL,
        role TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        description TEXT DEFAULT '',
        hours INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0
    );

    -- 目标公司
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        industry TEXT DEFAULT '',
        website TEXT DEFAULT '',
        career_page TEXT DEFAULT '',
        location TEXT DEFAULT '',
        size TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT ''
    );

    -- 目标岗位
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        url TEXT DEFAULT '',
        department TEXT DEFAULT '',
        city TEXT DEFAULT '',
        salary_range TEXT DEFAULT '',
        requirements TEXT DEFAULT '',
        description TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        applied_at TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT '',
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );

    -- 投递记录
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_id INTEGER NOT NULL,
        status TEXT DEFAULT 'draft',
        form_data TEXT DEFAULT '{}',
        filled_at TEXT DEFAULT '',
        submitted_at TEXT DEFAULT '',
        screenshot_path TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
