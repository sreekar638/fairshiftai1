from datetime import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/reports", tags=["Safety & Workplace Reports"])

def format_report_read(rep: models.SafetyReport) -> schemas.SafetyReportRead:
    reporter_name = "Anonymous Worker" if rep.is_anonymous or not rep.user else rep.user.full_name
    site_name = rep.organization.name if not rep.site_id else (
        [s.name for s in rep.organization.sites if s.id == rep.site_id] or [None]
    )[0]
    action_logs = [
        schemas.SafetyReportActionLogRead(
            id=log.id,
            action=log.action,
            notes=log.notes,
            timestamp=log.timestamp,
            actor_name="Reviewer" if not log.actor_id else "Authorized Supervisor"
        )
        for log in rep.action_logs
    ]
    return schemas.SafetyReportRead(
        id=rep.id,
        ref_number=rep.ref_number,
        org_id=rep.org_id,
        user_id=None if rep.is_anonymous else rep.user_id,
        site_id=rep.site_id,
        category=rep.category,
        title=rep.title,
        description=rep.description,
        priority=rep.priority,
        is_anonymous=rep.is_anonymous,
        status=rep.status,
        resolution_notes=rep.resolution_notes,
        reported_at=rep.reported_at,
        resolved_at=rep.resolved_at,
        reporter_name=reporter_name,
        site_name=site_name,
        action_logs=action_logs
    )

@router.post("", response_model=schemas.SafetyReportRead)
def submit_safety_report(
    payload: schemas.SafetyReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ref_seq = str(uuid.uuid4())[:8].upper()
    prefix = "SAF" if current_user.organization.industry == "construction" else "EDU"
    ref_number = f"{prefix}-2026-{ref_seq}"

    report = models.SafetyReport(
        ref_number=ref_number,
        org_id=current_user.org_id,
        user_id=None if payload.is_anonymous else current_user.id,
        site_id=payload.site_id or current_user.site_id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        is_anonymous=payload.is_anonymous,
        status="reported",
        reported_at=datetime.utcnow()
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Initial log
    log = models.ReportActionLog(
        report_id=report.id,
        actor_id=current_user.id if not payload.is_anonymous else None,
        action="Report filed",
        notes="Workplace safety report submitted to organization portal."
    )
    db.add(log)
    db.commit()
    db.refresh(report)

    return format_report_read(report)

@router.get("/my-reports", response_model=List[schemas.SafetyReportRead])
def get_my_reports(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = db.query(models.SafetyReport).filter(
        models.SafetyReport.org_id == current_user.org_id,
        models.SafetyReport.user_id == current_user.id
    ).order_by(models.SafetyReport.reported_at.desc()).all()
    return [format_report_read(r) for r in reports]

@router.get("", response_model=List[schemas.SafetyReportRead])
def get_all_reports_admin(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    query = db.query(models.SafetyReport).filter(
        models.SafetyReport.org_id == current_user.org_id
    )
    if status_filter:
        query = query.filter(models.SafetyReport.status == status_filter)
    if priority_filter:
        query = query.filter(models.SafetyReport.priority == priority_filter)
    if category_filter:
        query = query.filter(models.SafetyReport.category == category_filter)

    reports = query.order_by(models.SafetyReport.reported_at.desc()).all()
    return [format_report_read(r) for r in reports]

@router.patch("/{report_id}/status", response_model=schemas.SafetyReportRead)
def update_report_status(
    report_id: int,
    payload: schemas.SafetyReportStatusUpdate,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    report = db.query(models.SafetyReport).filter(
        models.SafetyReport.id == report_id,
        models.SafetyReport.org_id == current_user.org_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Safety report not found")

    old_status = report.status
    report.status = payload.status
    if payload.resolution_notes:
        report.resolution_notes = payload.resolution_notes
    if payload.status == "resolved" and not report.resolved_at:
        report.resolved_at = datetime.utcnow()

    # Log action
    log = models.ReportActionLog(
        report_id=report.id,
        actor_id=current_user.id,
        action=f"Status changed from {old_status} to {payload.status}",
        notes=payload.resolution_notes or "Status updated by authorized reviewer."
    )
    db.add(log)
    db.commit()
    db.refresh(report)
    return format_report_read(report)
