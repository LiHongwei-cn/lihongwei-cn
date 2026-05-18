from __future__ import annotations

import logging
from datetime import datetime, timedelta
from statistics import stdev

from backend.prompts.system_prompt import SYSTEM_PROMPT, MEDICAL_DISCLAIMER
from backend.prompts.weekly_report import build_weekly_prompt
from backend.services.deepseek import chat
from backend.services.medical import classify_bp, medication_summary

logger = logging.getLogger("bp-monitor")


def _week_boundaries(reference_date: str | None = None) -> tuple[str, str]:
    """Return (monday, sunday) ISO date strings for the week containing reference_date."""
    if reference_date:
        dt = datetime.fromisoformat(reference_date)
    else:
        dt = datetime.now()
    monday = dt - timedelta(days=dt.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


async def generate_report(
    user: dict,
    conn,
    week_start: str | None = None,
    week_end: str | None = None,
) -> dict:
    if week_start and week_end:
        ws, we = week_start, week_end
    else:
        ws, we = _week_boundaries()

    readings = conn.execute(
        """SELECT * FROM readings
           WHERE user_id = ? AND date(measured_at) >= ? AND date(measured_at) <= ?
           ORDER BY measured_at ASC""",
        (user["id"], ws, we),
    ).fetchall()

    if not readings:
        raise ValueError(f"本周（{ws} 至 {we}）暂无血压记录，无法生成报告")

    count = len(readings)
    sys_vals = [r["systolic"] for r in readings]
    dia_vals = [r["diastolic"] for r in readings]
    hr_vals = [r["heart_rate"] for r in readings if r["heart_rate"]]

    avg_sys = sum(sys_vals) / count
    avg_dia = sum(dia_vals) / count

    max_r = max(readings, key=lambda r: r["systolic"])
    min_r = min(readings, key=lambda r: r["systolic"])

    morning = [r["systolic"] for r in readings if r["time_period"] == "morning"]
    evening = [r["systolic"] for r in readings if r["time_period"] in ("evening", "night")]

    std_sys = stdev(sys_vals) if count >= 2 else 0.0
    std_dia = stdev(dia_vals) if count >= 2 else 0.0

    target_sys = user.get("target_systolic", 140)
    target_dia = user.get("target_diastolic", 90)
    in_range = sum(
        1 for r in readings
        if r["systolic"] <= target_sys and r["diastolic"] <= target_dia
    )
    time_in_range = (in_range / count) * 100

    level_counts: dict[str, int] = {}
    for r in readings:
        lvl = classify_bp(r["systolic"], r["diastolic"])
        level_counts[lvl] = level_counts.get(lvl, 0) + 1
    level_parts = [f"{lvl} {n}次（{n/count*100:.0f}%）" for lvl, n in level_counts.items()]
    level_distribution = "、".join(level_parts)

    days_set = {r["measured_at"][:10] for r in readings}
    expected = len(days_set) * 2
    compliance = min((count / expected) * 100, 100.0) if expected else 0.0

    daily: dict[str, list] = {}
    for r in readings:
        daily.setdefault(r["measured_at"][:10], []).append(r)
    daily_lines = []
    for d in sorted(daily):
        day_readings = daily[d]
        parts = []
        for r in day_readings:
            tp = r["time_period"] or "未知"
            parts.append(f"  {tp}：{r['systolic']}/{r['diastolic']}")
        daily_lines.append(f"- {d}：\n" + "\n".join(parts))
    daily_summary = "\n".join(daily_lines)

    meds_text = medication_summary(user.get("medications", "[]"))
    age = user.get("age")

    user_msg = build_weekly_prompt(
        age=age, target_systolic=target_sys, target_diastolic=target_dia,
        week_start=ws, week_end=we, medications=meds_text,
        reading_count=count, compliance_rate=compliance,
        avg_systolic=avg_sys, avg_diastolic=avg_dia,
        morning_avg=f"{sum(morning)/len(morning):.1f}" if morning else "无数据",
        evening_avg=f"{sum(evening)/len(evening):.1f}" if evening else "无数据",
        max_systolic=max_r["systolic"], max_diastolic=max_r["diastolic"],
        max_time=max_r["measured_at"],
        min_systolic=min_r["systolic"], min_diastolic=min_r["diastolic"],
        min_time=min_r["measured_at"],
        std_systolic=std_sys, std_diastolic=std_dia,
        time_in_range=time_in_range,
        level_distribution=level_distribution,
        daily_summary=daily_summary,
        disclaimer=MEDICAL_DISCLAIMER,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    ai_response = await chat(messages)

    report_data = {
        "user_id": user["id"],
        "week_start": ws,
        "week_end": we,
        "avg_systolic": round(avg_sys, 1),
        "avg_diastolic": round(avg_dia, 1),
        "avg_heart_rate": round(sum(hr_vals) / len(hr_vals), 1) if hr_vals else None,
        "max_systolic": max_r["systolic"],
        "max_diastolic": max_r["diastolic"],
        "min_systolic": min_r["systolic"],
        "min_diastolic": min_r["diastolic"],
        "std_systolic": round(std_sys, 1),
        "std_diastolic": round(std_dia, 1),
        "reading_count": count,
        "compliance_rate": round(compliance, 1),
        "morning_avg_sys": round(sum(morning) / len(morning), 1) if morning else None,
        "evening_avg_sys": round(sum(evening) / len(evening), 1) if evening else None,
        "time_in_range": round(time_in_range, 1),
        "trend_summary": ai_response,
        "recommendations": "",
    }

    conn.execute(
        """INSERT INTO reports (
            user_id, week_start, week_end, avg_systolic, avg_diastolic, avg_heart_rate,
            max_systolic, max_diastolic, min_systolic, min_diastolic,
            std_systolic, std_diastolic, reading_count, compliance_rate,
            morning_avg_sys, evening_avg_sys, time_in_range, trend_summary, recommendations
        ) VALUES (
            :user_id, :week_start, :week_end, :avg_systolic, :avg_diastolic, :avg_heart_rate,
            :max_systolic, :max_diastolic, :min_systolic, :min_diastolic,
            :std_systolic, :std_diastolic, :reading_count, :compliance_rate,
            :morning_avg_sys, :evening_avg_sys, :time_in_range, :trend_summary, :recommendations
        ) ON CONFLICT(user_id, week_start) DO UPDATE SET
            avg_systolic=excluded.avg_systolic, avg_diastolic=excluded.avg_diastolic,
            avg_heart_rate=excluded.avg_heart_rate,
            max_systolic=excluded.max_systolic, max_diastolic=excluded.max_diastolic,
            min_systolic=excluded.min_systolic, min_diastolic=excluded.min_diastolic,
            std_systolic=excluded.std_systolic, std_diastolic=excluded.std_diastolic,
            reading_count=excluded.reading_count, compliance_rate=excluded.compliance_rate,
            morning_avg_sys=excluded.morning_avg_sys, evening_avg_sys=excluded.evening_avg_sys,
            time_in_range=excluded.time_in_range, trend_summary=excluded.trend_summary,
            recommendations=excluded.recommendations
        """,
        report_data,
    )

    conn.execute(
        """INSERT INTO ai_feedback (user_id, prompt_type, prompt_text, response_text)
           VALUES (?, 'weekly_report', ?, ?)""",
        (user["id"], user_msg, ai_response),
    )
    conn.commit()

    report = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? AND week_start = ?",
        (user["id"], ws),
    ).fetchone()
    return dict(report)
