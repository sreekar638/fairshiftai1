from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserRead"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    org_id: Optional[int] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "worker"
    hourly_rate: float = 18.50
    worker_code: Optional[str] = None
    phone: Optional[str] = None
    language_pref: str = "en"
    site_id: Optional[int] = None

class UserCreate(UserBase):
    password: str
    org_id: int

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(UserBase):
    id: int
    org_id: int
    created_at: datetime
    organization_name: Optional[str] = None
    organization_industry: Optional[str] = None
    site_name: Optional[str] = None

    class Config:
        from_attributes = True

# Shift & Attendance Schemas
class CheckInOutRequest(BaseModel):
    method: str = "manual"  # 'qr' | 'manual'
    qr_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

class AttendanceEventRead(BaseModel):
    id: int
    shift_id: int
    event_type: str
    timestamp: datetime
    method: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class ShiftRead(BaseModel):
    id: int
    org_id: int
    user_id: int
    site_id: Optional[int] = None
    scheduled_start: datetime
    scheduled_end: datetime
    actual_check_in: Optional[datetime] = None
    actual_check_out: Optional[datetime] = None
    regular_hours: float
    overtime_hours: float
    status: str
    notes: Optional[str] = None
    user_name: Optional[str] = None
    site_name: Optional[str] = None

    class Config:
        from_attributes = True

# Payslip Schemas
class PayslipRead(BaseModel):
    id: int
    org_id: int
    user_id: int
    period_start: datetime
    period_end: datetime
    base_hourly_rate: float
    regular_hours: float
    overtime_hours: float
    overtime_rate: float
    allowances: float
    deductions: float
    gross_pay: float
    net_pay: float
    status: str
    synthetic_disclaimer: str
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

class PayslipGenerateRequest(BaseModel):
    user_id: int
    period_start: datetime
    period_end: datetime

# Safety Report Schemas
class SafetyReportCreate(BaseModel):
    category: str  # 'hazard' | 'equipment' | 'workload' | 'harassment' | 'pay_dispute' | 'maintenance'
    title: str
    description: str
    priority: str = "medium"  # 'low' | 'medium' | 'high' | 'critical'
    is_anonymous: bool = False
    site_id: Optional[int] = None

class SafetyReportStatusUpdate(BaseModel):
    status: str  # 'reported' | 'investigating' | 'resolved' | 'dismissed'
    resolution_notes: Optional[str] = None

class SafetyReportActionLogRead(BaseModel):
    id: int
    action: str
    notes: Optional[str] = None
    timestamp: datetime
    actor_name: Optional[str] = None

    class Config:
        from_attributes = True

class SafetyReportRead(BaseModel):
    id: int
    ref_number: str
    org_id: int
    user_id: Optional[int] = None
    site_id: Optional[int] = None
    category: str
    title: str
    description: str
    priority: str
    is_anonymous: bool
    status: str
    resolution_notes: Optional[str] = None
    reported_at: datetime
    resolved_at: Optional[datetime] = None
    reporter_name: Optional[str] = None
    site_name: Optional[str] = None
    action_logs: List[SafetyReportActionLogRead] = []

    class Config:
        from_attributes = True

# Feedback Schemas
class FeedbackCreate(BaseModel):
    site_id: Optional[int] = None
    condition_rating: int = Field(ge=1, le=5)
    workload_rating: int = Field(ge=1, le=5)
    break_rating: int = Field(ge=1, le=5)
    facility_rating: int = Field(ge=1, le=5)
    supervisor_rating: int = Field(ge=1, le=5)
    comments: Optional[str] = None
    is_anonymous: bool = True

class FeedbackAggregate(BaseModel):
    total_responses: int
    avg_condition: float
    avg_workload: float
    avg_breaks: float
    avg_facilities: float
    avg_supervisor: float
    recent_comments: List[str]

# Skill Passport Schemas
class SkillPassportCreate(BaseModel):
    title: str
    category: str
    issuer: str
    issue_date: datetime
    expiry_date: Optional[datetime] = None
    document_ref: Optional[str] = None

class SkillPassportVerify(BaseModel):
    is_verified: bool
    verification_notes: Optional[str] = None

class SkillPassportRead(BaseModel):
    id: int
    org_id: int
    user_id: int
    title: str
    category: str
    issuer: str
    issue_date: datetime
    expiry_date: Optional[datetime] = None
    is_verified: bool
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

# Fatigue Alert Schemas
class FatigueAlertRead(BaseModel):
    id: int
    org_id: int
    user_id: int
    shift_id: Optional[int] = None
    rule_code: str
    severity: str
    title: str
    details: str
    suggested_action: str
    status: str
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

# Analytics & Dashboard Schemas
class DashboardSummary(BaseModel):
    organization_name: str
    industry: str
    total_workers: int
    active_shifts_now: int
    total_hours_worked: float
    total_overtime_hours: float
    unresolved_safety_reports: int
    critical_fatigue_alerts: int
    average_worker_satisfaction: float
    verified_skills_percentage: float
    weekly_attendance_trend: List[Dict[str, Any]]
    fatigue_by_category: List[Dict[str, Any]]
    safety_by_category: List[Dict[str, Any]]

# AI Recommendation Schema
class AIRecommendation(BaseModel):
    category: str
    title: str
    observation: str
    evidence_metric: str
    recommended_action: str
    confidence: float
    source: str  # 'deterministic_rule' | 'gemini_pro'
