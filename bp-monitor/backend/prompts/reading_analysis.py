from __future__ import annotations

READING_ANALYSIS_TEMPLATE = """请分析以下血压读数：

**本次读数**
- 收缩压：{systolic} mmHg
- 舒张压：{diastolic} mmHg
- 心率：{heart_rate} bpm
- 测量时间：{measured_at}（{time_period_label}）
- 用户备注：{notes}

**用户信息**
- 年龄：{age}岁
- 性别：{gender}
- 高血压确诊年份：{diagnosis_year}
- 目标血压：{target_systolic}/{target_diastolic} mmHg
- 当前用药：{medications}

**最近7次历史读数**（从旧到新）
{recent_readings}

请按照以下格式回复：

📊 **本次读数分析**
[血压等级分类 + 是否在目标范围内 + 与历史趋势对比]

💊 **用药提醒**
[根据用户用药清单给出提醒，如测量时间是否需要调整、不可自行停药等]

🍽️ **生活方式建议**
[2-3条针对本次读数的具体建议，结合限盐、运动、情绪等因素]

⚠️ **注意事项**
[风险评估、需要关注的问题、是否需要就医]

{disclaimer}
"""

TIME_PERIOD_LABELS = {
    "morning": "早晨（起床后1小时内）",
    "afternoon": "下午",
    "evening": "晚上（睡前1小时内）",
    "night": "夜间",
}


def build_reading_prompt(
    systolic: int,
    diastolic: int,
    heart_rate: int | None,
    measured_at: str,
    time_period: str,
    notes: str,
    age: int | None,
    gender: str,
    diagnosis_year: int | None,
    medications: str,
    target_systolic: int,
    target_diastolic: int,
    recent_readings: str,
    disclaimer: str,
) -> str:
    hr_str = str(heart_rate) if heart_rate else "未记录"
    tp_label = TIME_PERIOD_LABELS.get(time_period, time_period or "未指定")
    age_str = str(age) if age else "未填写"
    gender_str = gender if gender else "未填写"
    diag_str = str(diagnosis_year) if diagnosis_year else "未填写"
    meds_str = medications if medications and medications != "[]" else "未填写"

    return READING_ANALYSIS_TEMPLATE.format(
        systolic=systolic,
        diastolic=diastolic,
        heart_rate=hr_str,
        measured_at=measured_at,
        time_period_label=tp_label,
        notes=notes or "无",
        age=age_str,
        gender=gender_str,
        diagnosis_year=diag_str,
        medications=meds_str,
        target_systolic=target_systolic,
        target_diastolic=target_diastolic,
        recent_readings=recent_readings,
        disclaimer=disclaimer,
    )
