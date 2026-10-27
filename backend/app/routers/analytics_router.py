from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/analytics", tags=["Workforce Analytics & Dashboard"])

@router.get("/dashboard", response_model=schemas.DashboardSummary)
def get_dashboard_summary(
    site_id: Optional[int] = None,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    org = current_user.organization

    # 1. Total Workers in organization
    workers_query = db.query(models.User).filter(
        models.User.org_id == org.id,
        models.User.role == "worker"
    )
    if site_id:
        workers_query = workers_query.filter(models.User.site_id == site_id)
    total_workers = workers_query.count()

    # 2. Active Shifts Right Now
    active_shifts_query = db.query(models.Shift).filter(
        models.Shift.org_id == org.id,
        models.Shift.status == "in_progress"
    )
    if site_id:
        active_shifts_query = active_shifts_query.filter(models.Shift.site_id == site_id)
    active_shifts_now = active_shifts_query.count()

    # 3. Total Regular & Overtime Hours
    shifts_query = db.query(models.Shift).filter(
        models.Shift.org_id == org.id,
        models.Shift.status == "completed"
    )
    if site_id:
        shifts_query = shifts_query.filter(models.Shift.site_id == site_id)
    completed_shifts = shifts_query.all()
    total_hours_worked = round(sum(s.regular_hours + s.overtime_hours for s in completed_shifts), 1)
    total_overtime_hours = round(sum(s.overtime_hours for s in completed_shifts), 1)

    # 4. Unresolved Safety Reports
    reports_query = db.query(models.SafetyReport).filter(
        models.SafetyReport.org_id == org.id,
        models.SafetyReport.status.in_(["reported", "investigating"])
    )
    if site_id:
        reports_query = reports_query.filter(models.SafetyReport.site_id == site_id)
    unresolved_safety = reports_query.count()

    # 5. Critical Fatigue Alerts
    fatigue_query = db.query(models.FatigueAlert).filter(
        models.FatigueAlert.org_id == org.id,
        models.FatigueAlert.severity == "critical",
        models.FatigueAlert.status == "active"
    )
    critical_fatigue = fatigue_query.count()

    # 6. Average Worker Satisfaction (Feedback)
    feedbacks_query = db.query(models.Feedback).filter(
        models.Feedback.org_id == org.id
    )
    if site_id:
        feedbacks_query = feedbacks_query.filter(models.Feedback.site_id == site_id)
    all_feedbacks = feedbacks_query.all()
    if all_feedbacks:
        avg_scores = [
            (f.condition_rating + f.workload_rating + f.break_rating + f.facility_rating + f.supervisor_rating) / 5.0
            for f in all_feedbacks
        ]
        avg_satisfaction = round(sum(avg_scores) / len(avg_scores), 2)
    else:
        avg_satisfaction = 4.5

    # 7. Verified Skills Percentage
    skills_query = db.query(models.SkillPassport).filter(
        models.SkillPassport.org_id == org.id
    )
    total_skills = skills_query.count()
    verified_skills = skills_query.filter(models.SkillPassport.is_verified == True).count()
    verified_percentage = round((verified_skills / total_skills) * 100, 1) if total_skills > 0 else 100.0

    # 8. Weekly Attendance Trend (Last 7 Days)
    now = datetime.utcnow()
    weekly_trend = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(6, -1, -1):
        target_day = now - timedelta(days=i)
        day_start = datetime(target_day.year, target_day.month, target_day.day, 0, 0, 0)
        day_end = day_start + timedelta(days=1)
        day_shifts = db.query(models.Shift).filter(
            models.Shift.org_id == org.id,
            models.Shift.actual_check_in >= day_start,
            models.Shift.actual_check_in < day_end
        ).all()
        day_reg = sum(s.regular_hours for s in day_shifts)
        day_ot = sum(s.overtime_hours for s in day_shifts)
        weekly_trend.append({
            "day": days[target_day.weekday()],
            "date": target_day.strftime("%b %d"),
            "regularHours": round(day_reg, 1),
            "overtimeHours": round(day_ot, 1),
            "attendees": len(day_shifts)
        })

    # 9. Fatigue by Category / Rule
    fatigue_rules = db.query(
        models.FatigueAlert.rule_code,
        func.count(models.FatigueAlert.id)
    ).filter(
        models.FatigueAlert.org_id == org.id
    ).group_by(models.FatigueAlert.rule_code).all()

    rule_labels = {
        "EXCESSIVE_HOURS_CRITICAL": "Shift > 12h",
        "EXCESSIVE_HOURS_WARNING": "Shift > 10h",
        "SHORT_REST_CRITICAL": "Rest < 8h",
        "SHORT_REST_WARNING": "Rest < 10h",
        "CONSECUTIVE_DAYS_LIMIT": "Consecutive Days (>6d)"
    }
    fatigue_by_category = [
        {"name": rule_labels.get(code, code), "value": count}
        for code, count in fatigue_rules
    ] or [{"name": "Normal Limits", "value": 1}]

    # 10. Safety Reports by Category
    safety_cats = db.query(
        models.SafetyReport.category,
        func.count(models.SafetyReport.id)
    ).filter(
        models.SafetyReport.org_id == org.id
    ).group_by(models.SafetyReport.category).all()

    safety_by_category = [
        {"name": cat.capitalize(), "count": count}
        for cat, count in safety_cats
    ]

    return schemas.DashboardSummary(
        organization_name=org.name,
        industry=org.industry,
        total_workers=total_workers,
        active_shifts_now=active_shifts_now,
        total_hours_worked=total_hours_worked,
        total_overtime_hours=total_overtime_hours,
        unresolved_safety_reports=unresolved_safety,
        critical_fatigue_alerts=critical_fatigue,
        average_worker_satisfaction=avg_satisfaction,
        verified_skills_percentage=verified_percentage,
        weekly_attendance_trend=weekly_trend,
        fatigue_by_category=fatigue_by_category,
        safety_by_category=safety_by_category
    )
