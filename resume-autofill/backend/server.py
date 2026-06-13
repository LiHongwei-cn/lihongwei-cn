"""FastAPI 后端 — 简历投递系统 API"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import get_conn, init_db

app = FastAPI(title="Resume AutoFill")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()


# ═══════════════════════════════════════════════
# Pydantic 模型
# ═══════════════════════════════════════════════

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    ethnicity: Optional[str] = None
    political_status: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    qq: Optional[str] = None
    hometown: Optional[str] = None
    current_city: Optional[str] = None
    current_address: Optional[str] = None
    university: Optional[str] = None
    college: Optional[str] = None
    major: Optional[str] = None
    degree: Optional[str] = None
    enrollment_year: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None
    ranking: Optional[str] = None
    target_position: Optional[str] = None
    target_city: Optional[str] = None
    expected_salary: Optional[str] = None
    available_date: Optional[str] = None
    photo_path: Optional[str] = None
    self_intro: Optional[str] = None
    skills: Optional[str] = None
    languages: Optional[str] = None
    hobbies: Optional[str] = None


class ItemCreate(BaseModel):
    data: dict


class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = ""
    website: Optional[str] = ""
    career_page: Optional[str] = ""
    location: Optional[str] = ""
    size: Optional[str] = ""
    notes: Optional[str] = ""


class PositionCreate(BaseModel):
    company_id: int
    title: str
    url: Optional[str] = ""
    department: Optional[str] = ""
    city: Optional[str] = ""
    salary_range: Optional[str] = ""
    requirements: Optional[str] = ""
    description: Optional[str] = ""


# ═══════════════════════════════════════════════
# 个人信息 API
# ═══════════════════════════════════════════════

@app.get("/api/profile")
def get_profile():
    conn = get_conn()
    row = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    if not row:
        return {}
    return dict(row)


@app.put("/api/profile")
def update_profile(data: ProfileUpdate):
    conn = get_conn()
    existing = conn.execute("SELECT id FROM profile WHERE id=1").fetchone()
    fields = {k: v for k, v in data.dict().items() if v is not None}
    fields["updated_at"] = datetime.now().isoformat()
    if existing:
        sets = ", ".join(f"{k}=?" for k in fields)
        conn.execute(f"UPDATE profile SET {sets} WHERE id=1", list(fields.values()))
    else:
        cols = ", ".join(fields.keys())
        placeholders = ", ".join(["?"] * len(fields))
        conn.execute(f"INSERT INTO profile ({cols}) VALUES ({placeholders})", list(fields.values()))
    conn.commit()
    conn.close()
    return {"ok": True}


# ═══════════════════════════════════════════════
# 通用 CRUD API
# ═══════════════════════════════════════════════

TABLES = {
    "education": ["school", "college", "major", "degree", "start_date", "end_date", "gpa", "ranking", "courses"],
    "projects": ["name", "role", "company", "start_date", "end_date", "description", "achievements", "tech_stack", "url"],
    "work_experience": ["company", "position", "start_date", "end_date", "description", "achievements"],
    "awards": ["name", "level", "issuer", "date", "description"],
    "certificates": ["name", "issuer", "date", "number", "expiry"],
    "organizations": ["name", "role", "start_date", "end_date", "description"],
    "publications": ["title", "authors", "venue", "date", "doi", "type"],
    "volunteer": ["organization", "role", "start_date", "end_date", "description", "hours"],
}


@app.get("/api/{table}")
def list_items(table: str):
    if table not in TABLES:
        raise HTTPException(404, f"未知表: {table}")
    conn = get_conn()
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY sort_order, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/{table}")
def create_item(table: str, body: ItemCreate):
    if table not in TABLES:
        raise HTTPException(404, f"未知表: {table}")
    allowed = set(TABLES[table])
    fields = {k: v for k, v in body.data.items() if k in allowed}
    if not fields:
        raise HTTPException(400, "无有效字段")
    conn = get_conn()
    cols = ", ".join(fields.keys())
    placeholders = ", ".join(["?"] * len(fields))
    cur = conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(fields.values()))
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return {"id": item_id, "ok": True}


@app.put("/api/{table}/{item_id}")
def update_item(table: str, item_id: int, body: ItemCreate):
    if table not in TABLES:
        raise HTTPException(404, f"未知表: {table}")
    allowed = set(TABLES[table])
    fields = {k: v for k, v in body.data.items() if k in allowed}
    if not fields:
        raise HTTPException(400, "无有效字段")
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in fields)
    conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", list(fields.values()) + [item_id])
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/{table}/{item_id}")
def delete_item(table: str, item_id: int):
    if table not in TABLES:
        raise HTTPException(404, f"未知表: {table}")
    conn = get_conn()
    conn.execute(f"DELETE FROM {table} WHERE id=?", [item_id])
    conn.commit()
    conn.close()
    return {"ok": True}


# ═══════════════════════════════════════════════
# 公司 & 岗位 API
# ═══════════════════════════════════════════════

@app.get("/api/companies")
def list_companies():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM companies ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/companies")
def create_company(body: CompanyCreate):
    conn = get_conn()
    now = datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO companies (name,industry,website,career_page,location,size,notes,created_at) VALUES (?,?,?,?,?,?,?,?)",
        [body.name, body.industry, body.website, body.career_page, body.location, body.size, body.notes, now]
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return {"id": cid, "ok": True}


@app.delete("/api/companies/{company_id}")
def delete_company(company_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM companies WHERE id=?", [company_id])
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/companies/{company_id}/positions")
def list_positions(company_id: int):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM positions WHERE company_id=? ORDER BY created_at DESC", [company_id]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/positions")
def create_position(body: PositionCreate):
    conn = get_conn()
    now = datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO positions (company_id,title,url,department,city,salary_range,requirements,description,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [body.company_id, body.title, body.url, body.department, body.city, body.salary_range, body.requirements, body.description, "pending", now]
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "ok": True}


@app.delete("/api/positions/{position_id}")
def delete_position(position_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM positions WHERE id=?", [position_id])
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/positions/all")
def list_all_positions():
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.*, c.name as company_name, c.career_page
        FROM positions p JOIN companies c ON p.company_id=c.id
        ORDER BY p.status, p.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.put("/api/positions/{position_id}/status")
def update_position_status(position_id: int, body: dict):
    status = body.get("status", "pending")
    conn = get_conn()
    updates = {"status": status}
    if status == "applied":
        updates["applied_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k}=?" for k in updates)
    conn.execute(f"UPDATE positions SET {sets} WHERE id=?", list(updates.values()) + [position_id])
    conn.commit()
    conn.close()
    return {"ok": True}


# ═══════════════════════════════════════════════
# 导出完整简历数据（给浏览器自动化用）
# ═══════════════════════════════════════════════

@app.get("/api/export")
def export_all():
    conn = get_conn()
    profile = dict(conn.execute("SELECT * FROM profile WHERE id=1").fetchone() or {})
    result = {"profile": profile}
    for table in TABLES:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY sort_order, id").fetchall()
        result[table] = [dict(r) for r in rows]
    conn.close()
    return result


# 静态文件服务
FRONTEND = Path(__file__).parent.parent / "frontend"
if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
