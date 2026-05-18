from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from backend.database import get_db, get_current_user
from backend.models import AIAnalysisResponse
from backend.services.analyzer import analyze_reading

router = APIRouter()

MAX_REANALYZE_PER_DAY = 5


@router.post("/analyze/{reading_id}", response_model=AIAnalysisResponse)
async def reanalyze(
    reading_id: int,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    today = date.today().isoformat()
    count = conn.execute(
        "SELECT COUNT(*) FROM ai_feedback WHERE user_id = ? AND date(created_at) = ? AND prompt_type = 'reading_analysis'",
        (user["id"], today),
    ).fetchone()[0]
    if count >= MAX_REANALYZE_PER_DAY:
        raise HTTPException(status_code=429, detail="今日重新分析次数已达上限")

    reading = conn.execute(
        "SELECT * FROM readings WHERE id = ? AND user_id = ?",
        (reading_id, user["id"]),
    ).fetchone()
    if not reading:
        raise HTTPException(status_code=404, detail="未找到该记录")

    analysis, bp_level = await analyze_reading(reading_id, user, conn)

    return AIAnalysisResponse(reading_id=reading_id, analysis=analysis, bp_level=bp_level)
