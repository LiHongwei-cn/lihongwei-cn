from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.database import get_db, get_current_user
from backend.models import (
    ReadingCreate, ReadingResponse, ReadingListResponse,
    StatsResponse, TrendsResponse,
)
from backend.services.analyzer import analyze_reading

router = APIRouter()

MAX_READINGS_PER_DAY = 10


def _check_rate_limit(user_id: int, conn) -> None:
    today = date.today().isoformat()
    count = conn.execute(
        "SELECT COUNT(*) FROM readings WHERE user_id = ? AND date(measured_at) = ?",
        (user_id, today),
    ).fetchone()[0]
    if count >= MAX_READINGS_PER_DAY:
        raise HTTPException(status_code=429, detail="今日记录次数已达上限，请明天继续记录")


@router.post("", response_model=ReadingResponse)
async def create_reading(
    body: ReadingCreate,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    _check_rate_limit(user["id"], conn)

    cursor = conn.execute(
        """INSERT INTO readings (user_id, systolic, diastolic, heart_rate, measured_at, time_period, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user["id"], body.systolic, body.diastolic, body.heart_rate,
         body.measured_at, body.time_period, body.notes),
    )
    reading_id = cursor.lastrowid
    conn.commit()

    analysis, bp_level = await analyze_reading(reading_id, user, conn)

    reading = conn.execute(
        "SELECT * FROM readings WHERE id = ?", (reading_id,)
    ).fetchone()
    return ReadingResponse(**dict(reading))


@router.get("", response_model=ReadingListResponse)
async def list_readings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: str = "",
    end_date: str = "",
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    conditions = ["user_id = ?"]
    params = [user["id"]]

    if start_date:
        conditions.append("date(measured_at) >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date(measured_at) <= ?")
        params.append(end_date)

    where = " AND ".join(conditions)

    total = conn.execute(
        f"SELECT COUNT(*) FROM readings WHERE {where}", params
    ).fetchone()[0]

    offset = (page - 1) * limit
    items = conn.execute(
        f"SELECT * FROM readings WHERE {where} ORDER BY measured_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()

    return ReadingListResponse(
        items=[ReadingResponse(**dict(r)) for r in items],
        total=total,
        page=page,
        has_more=offset + limit < total,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    days: int = Query(7, ge=1, le=365),
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    cutoff = f"date('now', '-{days} days')"
    rows = conn.execute(
        """SELECT systolic, diastolic, heart_rate, measured_at, time_period
           FROM readings
           WHERE user_id = ? AND date(measured_at) >= ?
           ORDER BY measured_at ASC""",
        (user["id"], cutoff),
    ).fetchall()

    if not rows:
        return StatsResponse(
            avg_systolic=0, avg_diastolic=0, avg_heart_rate=None,
            morning_avg_sys=None, evening_avg_sys=None,
            reading_count=0, days_with_readings=0,
            trend_direction="insufficient_data",
        )

    count = len(rows)
    days_set = {r["measured_at"][:10] for r in rows}

    sys_vals = [r["systolic"] for r in rows]
    dia_vals = [r["diastolic"] for r in rows]
    hr_vals = [r["heart_rate"] for r in rows if r["heart_rate"]]

    morning = [r["systolic"] for r in rows if r["time_period"] == "morning"]
    evening = [r["systolic"] for r in rows if r["time_period"] in ("evening", "night")]

    highest = max(rows, key=lambda r: r["systolic"])
    lowest = min(rows, key=lambda r: r["systolic"])

    if count >= 4:
        half = count // 2
        first_half_avg = sum(sys_vals[:half]) / half
        second_half_avg = sum(sys_vals[half:]) / (count - half)
        diff = second_half_avg - first_half_avg
        if diff < -5:
            direction = "improving"
        elif diff > 5:
            direction = "worsening"
        else:
            direction = "stable"
    else:
        direction = "insufficient_data"

    return StatsResponse(
        avg_systolic=round(sum(sys_vals) / count, 1),
        avg_diastolic=round(sum(dia_vals) / count, 1),
        avg_heart_rate=round(sum(hr_vals) / len(hr_vals), 1) if hr_vals else None,
        morning_avg_sys=round(sum(morning) / len(morning), 1) if morning else None,
        evening_avg_sys=round(sum(evening) / len(evening), 1) if evening else None,
        reading_count=count,
        days_with_readings=len(days_set),
        trend_direction=direction,
        highest={"systolic": highest["systolic"], "diastolic": highest["diastolic"], "measured_at": highest["measured_at"]},
        lowest={"systolic": lowest["systolic"], "diastolic": lowest["diastolic"], "measured_at": lowest["measured_at"]},
    )


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    cutoff = f"date('now', '-{days} days')"
    rows = conn.execute(
        """SELECT date(measured_at) as d, systolic, diastolic, heart_rate
           FROM readings
           WHERE user_id = ? AND date(measured_at) >= ?
           ORDER BY measured_at ASC""",
        (user["id"], cutoff),
    ).fetchall()

    dates: list[str] = []
    systolic: list[int | None] = []
    diastolic: list[int | None] = []
    heart_rate: list[int | None] = []

    day_data: dict[str, list] = {}
    for r in rows:
        day_data.setdefault(r["d"], []).append(r)

    for d, day_rows in day_data.items():
        dates.append(d)
        systolic.append(round(sum(r["systolic"] for r in day_rows) / len(day_rows)))
        diastolic.append(round(sum(r["diastolic"] for r in day_rows) / len(day_rows)))
        hr_vals = [r["heart_rate"] for r in day_rows if r["heart_rate"]]
        heart_rate.append(round(sum(hr_vals) / len(hr_vals)) if hr_vals else None)

    return TrendsResponse(dates=dates, systolic=systolic, diastolic=diastolic, heart_rate=heart_rate)


@router.get("/{reading_id}", response_model=ReadingResponse)
async def get_reading(
    reading_id: int,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    reading = conn.execute(
        "SELECT * FROM readings WHERE id = ? AND user_id = ?",
        (reading_id, user["id"]),
    ).fetchone()
    if not reading:
        raise HTTPException(status_code=404, detail="未找到该记录")
    return ReadingResponse(**dict(reading))
