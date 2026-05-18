import logging

from backend.prompts.system_prompt import SYSTEM_PROMPT, MEDICAL_DISCLAIMER
from backend.prompts.reading_analysis import build_reading_prompt
from backend.services.deepseek import chat
from backend.services.medical import classify_bp, is_emergency, medication_summary

logger = logging.getLogger("bp-monitor")


async def analyze_reading(reading_id: int, user: dict, conn: sqlite3.Connection) -> tuple[str, str]:
    """Analyze a single reading. Returns (analysis_text, bp_level)."""

    reading = conn.execute(
        "SELECT * FROM readings WHERE id = ?", (reading_id,)
    ).fetchone()
    if not reading:
        return "读取数据失败", ""

    bp_level = classify_bp(reading["systolic"], reading["diastolic"])
    emergency = is_emergency(reading["systolic"], reading["diastolic"], reading["notes"] or "")

    if emergency:
        analysis = (
            "⚠️ **紧急提醒** ⚠️\n\n"
            f"您的血压读数为 {reading['systolic']}/{reading['diastolic']} mmHg，"
            "已达到需立即就医的水平。\n\n"
            "**请立即拨打120或前往最近的医院急诊科。**\n\n"
            "您的血压数据已安全保存，可供医生参考。"
            f"{MEDICAL_DISCLAIMER}"
        )
        conn.execute(
            "UPDATE readings SET ai_analysis = ?, bp_level = ? WHERE id = ?",
            (analysis, bp_level, reading_id),
        )
        conn.commit()
        return analysis, bp_level

    recent = conn.execute(
        """SELECT systolic, diastolic, heart_rate, measured_at, time_period, bp_level
           FROM readings WHERE user_id = ? AND id != ?
           ORDER BY measured_at DESC LIMIT 7""",
        (user["id"], reading_id),
    ).fetchall()

    if recent:
        lines = []
        for r in reversed(recent):
            hr_str = f"心率{r['heart_rate']}" if r["heart_rate"] else ""
            level_str = f" [{r['bp_level']}]" if r["bp_level"] else ""
            lines.append(
                f"- {r['measured_at']}（{r['time_period'] or '未指定'}）："
                f"{r['systolic']}/{r['diastolic']} {hr_str}{level_str}"
            )
        recent_text = "\n".join(lines)
    else:
        recent_text = "（暂无历史记录）"

    meds_text = medication_summary(user.get("medications", "[]"))

    user_msg = build_reading_prompt(
        systolic=reading["systolic"],
        diastolic=reading["diastolic"],
        heart_rate=reading["heart_rate"],
        measured_at=reading["measured_at"],
        time_period=reading["time_period"] or "",
        notes=reading["notes"] or "",
        age=user.get("age"),
        gender=user.get("gender", ""),
        diagnosis_year=user.get("diagnosis_year"),
        medications=meds_text,
        target_systolic=user.get("target_systolic", 140),
        target_diastolic=user.get("target_diastolic", 90),
        recent_readings=recent_text,
        disclaimer=MEDICAL_DISCLAIMER,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    analysis = await chat(messages)

    conn.execute(
        "UPDATE readings SET ai_analysis = ?, bp_level = ? WHERE id = ?",
        (analysis, bp_level, reading_id),
    )

    conn.execute(
        """INSERT INTO ai_feedback (user_id, reading_id, prompt_type, prompt_text, response_text)
           VALUES (?, ?, 'reading_analysis', ?, ?)""",
        (user["id"], reading_id, user_msg, analysis),
    )
    conn.commit()

    return analysis, bp_level
