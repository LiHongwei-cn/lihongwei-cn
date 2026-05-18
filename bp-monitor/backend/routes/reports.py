from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.config import CRON_SECRET_TOKEN
from backend.database import get_db, get_current_user
from backend.models import ReportResponse
from backend.services.report_gen import generate_report

router = APIRouter()


async def get_user_or_cron(
    x_cron_token: Optional[str] = Header(None),
    user: Optional[dict] = Depends(get_current_user),
):
    if user:
        return user
    if x_cron_token and x_cron_token == CRON_SECRET_TOKEN:
        return None  # cron caller, no specific user
    raise HTTPException(status_code=401, detail="请先登录")


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    reports = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY week_start DESC LIMIT 52",
        (user["id"],),
    ).fetchall()
    return [ReportResponse(**dict(r)) for r in reports]


@router.get("/latest", response_model=ReportResponse)
async def latest_report(
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    report = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY week_start DESC LIMIT 1",
        (user["id"],),
    ).fetchone()
    if not report:
        raise HTTPException(status_code=404, detail="暂无报告，请先生成")
    return ReportResponse(**dict(report))


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    report = conn.execute(
        "SELECT * FROM reports WHERE id = ? AND user_id = ?",
        (report_id, user["id"]),
    ).fetchone()
    if not report:
        raise HTTPException(status_code=404, detail="未找到该报告")
    return ReportResponse(**dict(report))


@router.post("/generate", response_model=ReportResponse)
async def trigger_report(
    all_users: bool = False,
    user: Optional[dict] = Depends(get_user_or_cron),
    conn=Depends(get_db),
):
    if all_users:
        users = conn.execute("SELECT * FROM users").fetchall()
        results = []
        for u in users:
            try:
                report = await generate_report(dict(u), conn)
                results.append(report)
            except ValueError:
                continue
        if not results:
            raise HTTPException(status_code=400, detail="本周暂无用户有血压记录")
        return ReportResponse(**results[0])

    if not user:
        raise HTTPException(status_code=400, detail="请指定用户")

    try:
        report = await generate_report(user, conn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ReportResponse(**report)
