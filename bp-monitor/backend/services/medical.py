def classify_bp(systolic: int, diastolic: int) -> str:
    """Classify blood pressure level per WHO/ISH + Chinese guidelines."""
    if systolic >= 180 or diastolic >= 110:
        return "3级高血压（重度）"
    if systolic >= 160 or diastolic >= 100:
        return "2级高血压（中度）"
    if systolic >= 140 or diastolic >= 90:
        return "1级高血压（轻度）"
    if systolic >= 130 or diastolic >= 85:
        return "正常高值"
    if systolic >= 120 or diastolic >= 80:
        return "正常血压"
    return "理想血压"


def is_emergency(systolic: int, diastolic: int, notes: str = "") -> bool:
    """Check if reading meets emergency criteria."""
    if systolic >= 180 or diastolic >= 110:
        emergency_keywords = ["头痛", "视力模糊", "胸闷", "呼吸困难", "头晕",
                              "胸痛", "说不清话", "无力", "恶心"]
        if any(kw in (notes or "") for kw in emergency_keywords):
            return True
    if systolic < 90:
        return True
    return False


def in_target_range(
    systolic: int, diastolic: int,
    target_sys: int, target_dia: int,
) -> bool:
    return systolic <= target_sys and diastolic <= target_dia


def medication_summary(medications_json: str) -> str:
    """Parse medications JSON into readable string."""
    import json
    try:
        meds = json.loads(medications_json)
    except (json.JSONDecodeError, TypeError):
        return "未填写"
    if not meds:
        return "未填写"
    parts = []
    for m in meds:
        name = m.get("name", "")
        dose = m.get("dose", "")
        timing = m.get("time", "")
        parts.append(f"{name} {dose}（{timing}）" if dose else name)
    return "、".join(parts)
