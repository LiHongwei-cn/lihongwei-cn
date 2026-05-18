from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Reading ──────────────────────────────────────────────────

SYSTOLIC_RANGE = (60, 300)
DIASTOLIC_RANGE = (30, 200)
HR_RANGE = (30, 250)
VALID_TIME_PERIODS = {"morning", "afternoon", "evening", "night", ""}


class ReadingCreate(BaseModel):
    systolic: int = Field(..., ge=SYSTOLIC_RANGE[0], le=SYSTOLIC_RANGE[1])
    diastolic: int = Field(..., ge=DIASTOLIC_RANGE[0], le=DIASTOLIC_RANGE[1])
    heart_rate: Optional[int] = Field(None, ge=HR_RANGE[0], le=HR_RANGE[1])
    measured_at: str  # ISO 8601
    time_period: str = ""
    notes: str = ""

    @field_validator("time_period")
    @classmethod
    def check_time_period(cls, v: str) -> str:
        if v not in VALID_TIME_PERIODS:
            return ""
        return v

    @field_validator("notes")
    @classmethod
    def truncate_notes(cls, v: str) -> str:
        return v[:200]


class ReadingResponse(BaseModel):
    id: int
    user_id: int
    systolic: int
    diastolic: int
    heart_rate: Optional[int]
    measured_at: str
    time_period: str
    notes: str
    ai_analysis: str
    bp_level: str
    created_at: str


class ReadingListResponse(BaseModel):
    items: list[ReadingResponse]
    total: int
    page: int
    has_more: bool


class StatsResponse(BaseModel):
    avg_systolic: float
    avg_diastolic: float
    avg_heart_rate: Optional[float]
    morning_avg_sys: Optional[float]
    evening_avg_sys: Optional[float]
    reading_count: int
    days_with_readings: int
    trend_direction: str  # "improving" | "stable" | "worsening" | "insufficient_data"
    highest: Optional[dict] = None
    lowest: Optional[dict] = None


class TrendsResponse(BaseModel):
    dates: list[str]
    systolic: list[Optional[int]]
    diastolic: list[Optional[int]]
    heart_rate: list[Optional[int]]


# ── Auth ─────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    token: str
    user: "UserProfile"


# ── User ─────────────────────────────────────────────────────

class UserProfile(BaseModel):
    id: int
    openid: str = ""
    nickname: str = ""
    avatar_url: str = ""
    age: Optional[int] = None
    gender: str = ""
    diagnosis_year: Optional[int] = None
    medications: str = "[]"
    target_systolic: int = 140
    target_diastolic: int = 90
    disclaimer_accepted: int = 0


class UserUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis_year: Optional[int] = None
    medications: Optional[str] = None
    target_systolic: Optional[int] = Field(None, ge=100, le=200)
    target_diastolic: Optional[int] = Field(None, ge=60, le=120)


# ── Report ───────────────────────────────────────────────────

class ReportResponse(BaseModel):
    id: int
    user_id: int
    week_start: str
    week_end: str
    avg_systolic: Optional[float]
    avg_diastolic: Optional[float]
    avg_heart_rate: Optional[float]
    max_systolic: Optional[int]
    max_diastolic: Optional[int]
    min_systolic: Optional[int]
    min_diastolic: Optional[int]
    std_systolic: Optional[float]
    std_diastolic: Optional[float]
    reading_count: int
    compliance_rate: float
    morning_avg_sys: Optional[float]
    evening_avg_sys: Optional[float]
    time_in_range: float
    trend_summary: str
    recommendations: str
    created_at: str


# ── AI ───────────────────────────────────────────────────────

class AIAnalysisResponse(BaseModel):
    reading_id: int
    analysis: str
    bp_level: str
