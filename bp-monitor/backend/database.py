import sqlite3
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.config import DB_PATH

security = HTTPBearer(auto_error=False)

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    openid          TEXT UNIQUE NOT NULL,
    session_token   TEXT,
    nickname        TEXT DEFAULT '',
    avatar_url      TEXT DEFAULT '',
    age             INTEGER,
    gender          TEXT DEFAULT '',
    diagnosis_year  INTEGER,
    medications     TEXT DEFAULT '[]',
    target_systolic  INTEGER DEFAULT 140,
    target_diastolic INTEGER DEFAULT 90,
    disclaimer_accepted INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS readings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    systolic        INTEGER NOT NULL,
    diastolic       INTEGER NOT NULL,
    heart_rate      INTEGER,
    measured_at     TEXT NOT NULL,
    time_period     TEXT DEFAULT '',
    notes           TEXT DEFAULT '',
    ai_analysis     TEXT DEFAULT '',
    bp_level        TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_readings_user_time
    ON readings(user_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    week_start      TEXT NOT NULL,
    week_end        TEXT NOT NULL,
    avg_systolic    REAL,
    avg_diastolic   REAL,
    avg_heart_rate  REAL,
    max_systolic    INTEGER,
    max_diastolic   INTEGER,
    min_systolic    INTEGER,
    min_diastolic   INTEGER,
    std_systolic    REAL,
    std_diastolic   REAL,
    reading_count   INTEGER DEFAULT 0,
    compliance_rate REAL DEFAULT 0.0,
    morning_avg_sys REAL,
    evening_avg_sys REAL,
    time_in_range   REAL DEFAULT 0.0,
    trend_summary   TEXT DEFAULT '',
    recommendations TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, week_start)
);

CREATE TABLE IF NOT EXISTS ai_feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    reading_id      INTEGER,
    prompt_type     TEXT NOT NULL,
    prompt_text     TEXT NOT NULL,
    response_text   TEXT NOT NULL,
    tokens_used     INTEGER,
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (reading_id) REFERENCES readings(id)
);
"""


def init_db() -> None:
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="请先登录")

    token = credentials.credentials

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE session_token = ?", (token,)
        ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="登录已过期，请重新打开小程序")
        return dict(user)
    finally:
        conn.close()
