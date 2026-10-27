import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    industry = Column(String(50), nullable=False)  # 'construction' | 'education' | 'hospital' | 'factory'
    code = Column(String(50), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="organization")
    sites = relationship("SiteOrDepartment", back_populates="organization")
    reports = relationship("SafetyReport", back_populates="organization")
    shifts = relationship("Shift", back_populates="organization")

class SiteOrDepartment(Base):
    __tablename__ = "sites_departments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(120), nullable=False)
    facility_type = Column(String(50), default="site")  # 'site' or 'department'
    location = Column(String(200), nullable=True)
    qr_token = Column(String(100), unique=True, index=True)

    organization = relationship("Organization", back_populates="sites")
    shifts = relationship("Shift", back_populates="site")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites_departments.id"), nullable=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(30), nullable=False, default="worker")  # 'worker' | 'supervisor' | 'admin'
    hourly_rate = Column(Float, default=18.50)
    worker_code = Column(String(50), index=True, nullable=True)
    phone = Column(String(30), nullable=True)
    language_pref = Column(String(10), default="en")  # 'en' | 'ta'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="users")
    shifts = relationship("Shift", back_populates="user")
    payslips = relationship("Payslip", back_populates="user")
    skills = relationship("SkillPassport", back_populates="user")
    fatigue_alerts = relationship("FatigueAlert", back_populates="user")

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites_departments.id"), nullable=True)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_check_in = Column(DateTime, nullable=True)
    actual_check_out = Column(DateTime, nullable=True)
    regular_hours = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    status = Column(String(30), default="scheduled")  # 'scheduled' | 'in_progress' | 'completed' | 'missed'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="shifts")
    user = relationship("User", back_populates="shifts")
    site = relationship("SiteOrDepartment", back_populates="shifts")
    events = relationship("AttendanceEvent", back_populates="shift", cascade="all, delete-orphan")

class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(20), nullable=False)  # 'check_in' | 'check_out'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    method = Column(String(20), default="manual")  # 'qr' | 'manual'
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(String(255), nullable=True)

    shift = relationship("Shift", back_populates="events")

class Payslip(Base):
    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    base_hourly_rate = Column(Float, nullable=False)
    regular_hours = Column(Float, nullable=False, default=0.0)
    overtime_hours = Column(Float, nullable=False, default=0.0)
    overtime_rate = Column(Float, nullable=False, default=1.5)
    allowances = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    gross_pay = Column(Float, nullable=False)
    net_pay = Column(Float, nullable=False)
    status = Column(String(30), default="generated")  # 'generated' | 'approved' | 'paid'
    synthetic_disclaimer = Column(
        String(255),
        default="Synthetic demonstration payslip for FairShift AI — not legal tax/wage counsel."
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="payslips")

class SafetyReport(Base):
    __tablename__ = "safety_reports"

    id = Column(Integer, primary_key=True, index=True)
    ref_number = Column(String(30), unique=True, index=True, nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null if strictly anonymous
    site_id = Column(Integer, ForeignKey("sites_departments.id"), nullable=True)
    category = Column(String(50), nullable=False)  # 'hazard' | 'equipment' | 'workload' | 'harassment' | 'pay_dispute' | 'maintenance'
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")  # 'low' | 'medium' | 'high' | 'critical'
    is_anonymous = Column(Boolean, default=False)
    status = Column(String(30), default="reported")  # 'reported' | 'investigating' | 'resolved' | 'dismissed'
    resolution_notes = Column(Text, nullable=True)
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="reports")
    action_logs = relationship("ReportActionLog", back_populates="report", cascade="all, delete-orphan")

class ReportActionLog(Base):
    __tablename__ = "report_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(80), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    report = relationship("SafetyReport", back_populates="action_logs")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites_departments.id"), nullable=True)
    condition_rating = Column(Integer, nullable=False)  # 1 to 5
    workload_rating = Column(Integer, nullable=False)   # 1 to 5
    break_rating = Column(Integer, nullable=False)      # 1 to 5
    facility_rating = Column(Integer, nullable=False)   # 1 to 5
    supervisor_rating = Column(Integer, nullable=False) # 1 to 5
    comments = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SkillPassport(Base):
    __tablename__ = "skill_passport"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(120), nullable=False)
    category = Column(String(60), nullable=False)  # 'safety' | 'technical' | 'machinery' | 'pedagogy' | 'first_aid'
    issuer = Column(String(120), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(120), nullable=True)
    verification_notes = Column(String(255), nullable=True)
    document_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="skills")

class FatigueAlert(Base):
    __tablename__ = "fatigue_alerts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True)
    rule_code = Column(String(50), nullable=False)  # 'EXCESSIVE_HOURS' | 'CONSECUTIVE_DAYS' | 'SHORT_REST'
    severity = Column(String(20), default="warning")  # 'info' | 'warning' | 'critical'
    title = Column(String(180), nullable=False)
    details = Column(Text, nullable=False)
    suggested_action = Column(String(255), nullable=False)
    status = Column(String(30), default="active")  # 'active' | 'acknowledged' | 'resolved'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="fatigue_alerts")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    payload = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
