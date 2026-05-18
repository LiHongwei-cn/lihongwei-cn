from __future__ import annotations

WEEKLY_REPORT_TEMPLATE = """请根据以下一周血压数据生成综合健康周报：

**基本信息**
- 用户年龄：{age}岁
- 目标血压：{target_systolic}/{target_diastolic} mmHg
- 报告周期：{week_start} 至 {week_end}
- 当前用药：{medications}

**本周统计**
- 总测量次数：{reading_count} 次（目标：14次，早晚各一次）
- 达标率：{compliance_rate}%
- 平均血压：{avg_systolic}/{avg_diastolic} mmHg
- 早晨平均：{morning_avg} mmHg
- 晚上平均：{evening_avg} mmHg
- 最高血压：{max_systolic}/{max_diastolic} mmHg（{max_time}）
- 最低血压：{min_systolic}/{min_diastolic} mmHg（{min_time}）
- 血压波动（标准差）：收缩压±{std_systolic}，舒张压±{std_diastolic}
- 目标范围内时间占比：{time_in_range}%
- 血压分级分布：{level_distribution}

**每日摘要**
{daily_summary}

请按以下格式回复：

📈 **本周血压趋势**
[整体趋势分析（改善/稳定/恶化），与目标对比，波动情况评估]

🔍 **关键发现**
[2-3个最重要的发现，如晨峰现象、傍晚升高、特定日的异常等]

💊 **用药管理**
[用药依从性评估、服用时间是否合理、是否需要与医生讨论调药]

🏃 **生活方式评估**
[根据本周血压模式给出饮食、运动、盐摄入、情绪管理建议]

🎯 **下周目标**
[1-2个具体可量化的健康目标]

{disclaimer}
"""


def build_weekly_prompt(
    age: int | None,
    target_systolic: int,
    target_diastolic: int,
    week_start: str,
    week_end: str,
    medications: str,
    reading_count: int,
    compliance_rate: float,
    avg_systolic: float,
    avg_diastolic: float,
    morning_avg: str,
    evening_avg: str,
    max_systolic: int,
    max_diastolic: int,
    max_time: str,
    min_systolic: int,
    min_diastolic: int,
    min_time: str,
    std_systolic: float,
    std_diastolic: float,
    time_in_range: float,
    level_distribution: str,
    daily_summary: str,
    disclaimer: str,
) -> str:
    age_str = str(age) if age else "未填写"
    meds_str = medications if medications and medications != "[]" else "未填写"

    return WEEKLY_REPORT_TEMPLATE.format(
        age=age_str,
        target_systolic=target_systolic,
        target_diastolic=target_diastolic,
        week_start=week_start,
        week_end=week_end,
        medications=meds_str,
        reading_count=reading_count,
        compliance_rate=f"{compliance_rate:.1f}",
        avg_systolic=f"{avg_systolic:.1f}",
        avg_diastolic=f"{avg_diastolic:.1f}",
        morning_avg=morning_avg,
        evening_avg=evening_avg,
        max_systolic=max_systolic,
        max_diastolic=max_diastolic,
        max_time=max_time,
        min_systolic=min_systolic,
        min_diastolic=min_diastolic,
        min_time=min_time,
        std_systolic=f"{std_systolic:.1f}",
        std_diastolic=f"{std_diastolic:.1f}",
        time_in_range=f"{time_in_range:.1f}",
        level_distribution=level_distribution,
        daily_summary=daily_summary,
        disclaimer=disclaimer,
    )
