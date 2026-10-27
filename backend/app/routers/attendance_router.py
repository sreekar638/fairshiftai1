from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_roles
from app.fatigue_engine import FatigueRuleEngine

router = APIRouter(prefix="/attendance", tags=["Attendance & Shifts"])

@router.get("/sites")
def list_sites(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sites = db.query(models.SiteOrDepartment).filter(
        models.SiteOrDepartment.org_id == current_user.org_id
    ).all()
    return [{
        "id": s.id,
        "name": s.name,
        "facility_type": s.facility_type,
        "location": s.location,
        "qr_token": s.qr_token
    } for s in sites]

@router.get("/my-shifts", response_model=List[schemas.ShiftRead])
def get_my_shifts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shifts = db.query(models.Shift).filter(
        models.Shift.user_id == current_user.id
    ).order_by(models.Shift.scheduled_start.desc()).all()

    result = []
    for s in shifts:
        site_name = s.site.name if s.site else None
        result.append(schemas.ShiftRead(
            id=s.id,
            org_id=s.org_id,
            user_id=s.user_id,
            site_id=s.site_id,
            scheduled_start=s.scheduled_start,
            scheduled_end=s.scheduled_end,
            actual_check_in=s.actual_check_in,
            actual_check_out=s.actual_check_out,
            regular_hours=s.regular_hours,
            overtime_hours=s.overtime_hours,
            status=s.status,
            notes=s.notes,
            user_name=current_user.full_name,
            site_name=site_name
        ))
    return result

@router.post("/check-in", response_model=schemas.ShiftRead)
def check_in(
    payload: schemas.CheckInOutRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Prevent duplicate active shifts
    existing_active = db.query(models.Shift).filter(
        models.Shift.user_id == current_user.id,
        models.Shift.status == "in_progress"
    ).first()
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active shift in progress. Please check out first."
        )

    # 2. Validate QR token if method is 'qr'
    site_id = current_user.site_id
    if payload.method == "qr":
        if not payload.qr_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR Token is required for QR-based check-in."
            )
        site = db.query(models.SiteOrDepartment).filter(
            models.SiteOrDepartment.org_id == current_user.org_id,
            models.SiteOrDepartment.qr_token == payload.qr_token
        ).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or unrecognized site QR code."
            )
        site_id = site.id

    now = datetime.utcnow()
    # Check if a scheduled shift exists for today
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
    today_end = today_start + timedelta(days=1)
    shift = db.query(models.Shift).filter(
        models.Shift.user_id == current_user.id,
        models.Shift.scheduled_start >= today_start,
        models.Shift.scheduled_start < today_end,
        models.Shift.status == "scheduled"
    ).first()

    if not shift:
        # Create ad-hoc shift
        shift = models.Shift(
            org_id=current_user.org_id,
            user_id=current_user.id,
            site_id=site_id,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=8),
            status="scheduled"
        )
        db.add(shift)
        db.commit()
        db.refresh(shift)

    shift.actual_check_in = now
    shift.status = "in_progress"
    if payload.notes:
        shift.notes = (shift.notes or "") + f" [Check-in: {payload.notes}]"

    # Log attendance event
    event = models.AttendanceEvent(
        shift_id=shift.id,
        user_id=current_user.id,
        event_type="check_in",
        timestamp=now,
        method=payload.method,
        latitude=payload.latitude,
        longitude=payload.longitude,
        notes=payload.notes
    )
    db.add(event)
    db.commit()
    db.refresh(shift)

    site_name = shift.site.name if shift.site else None
    return schemas.ShiftRead(
        id=shift.id,
        org_id=shift.org_id,
        user_id=shift.user_id,
        site_id=shift.site_id,
        scheduled_start=shift.scheduled_start,
        scheduled_end=shift.scheduled_end,
        actual_check_in=shift.actual_check_in,
        actual_check_out=shift.actual_check_out,
        regular_hours=shift.regular_hours,
        overtime_hours=shift.overtime_hours,
        status=shift.status,
        notes=shift.notes,
        user_name=current_user.full_name,
        site_name=site_name
    )

@router.post("/check-out", response_model=schemas.ShiftRead)
def check_out(
    payload: schemas.CheckInOutRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find active shift
    shift = db.query(models.Shift).filter(
        models.Shift.user_id == current_user.id,
        models.Shift.status == "in_progress"
    ).first()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active shift found to check out from."
        )

    now = datetime.utcnow()
    shift.actual_check_out = now
    shift.status = "completed"

    # Calculate hours
    total_hours = max(0.1, (now - shift.actual_check_in).total_seconds() / 3600.0)
    shift.regular_hours = round(min(8.0, total_hours), 2)
    shift.overtime_hours = round(max(0.0, total_hours - 8.0), 2)
    if payload.notes:
        shift.notes = (shift.notes or "") + f" [Check-out: {payload.notes}]"

    # Log event
    event = models.AttendanceEvent(
        shift_id=shift.id,
        user_id=current_user.id,
        event_type="check_out",
        timestamp=now,
        method=payload.method,
        latitude=payload.latitude,
        longitude=payload.longitude,
        notes=payload.notes
    )
    db.add(event)
    db.commit()
    db.refresh(shift)

    # Trigger Fatigue Engine automatically
    FatigueRuleEngine.evaluate_shift(db, shift)

    site_name = shift.site.name if shift.site else None
    return schemas.ShiftRead(
        id=shift.id,
        org_id=shift.org_id,
        user_id=shift.user_id,
        site_id=shift.site_id,
        scheduled_start=shift.scheduled_start,
        scheduled_end=shift.scheduled_end,
        actual_check_in=shift.actual_check_in,
        actual_check_out=shift.actual_check_out,
        regular_hours=shift.regular_hours,
        overtime_hours=shift.overtime_hours,
        status=shift.status,
        notes=shift.notes,
        user_name=current_user.full_name,
        site_name=site_name
    )

@router.get("/all-shifts", response_model=List[schemas.ShiftRead])
def get_all_shifts_admin(
    site_id: Optional[int] = None,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    query = db.query(models.Shift).filter(models.Shift.org_id == current_user.org_id)
    if site_id:
        query = query.filter(models.Shift.site_id == site_id)
    shifts = query.order_by(models.Shift.scheduled_start.desc()).limit(100).all()

    result = []
    for s in shifts:
        user_name = s.user.full_name if s.user else "Worker"
        site_name = s.site.name if s.site else None
        result.append(schemas.ShiftRead(
            id=s.id,
            org_id=s.org_id,
            user_id=s.user_id,
            site_id=s.site_id,
            scheduled_start=s.scheduled_start,
            scheduled_end=s.scheduled_end,
            actual_check_in=s.actual_check_in,
            actual_check_out=s.actual_check_out,
            regular_hours=s.regular_hours,
            overtime_hours=s.overtime_hours,
            status=s.status,
            notes=s.notes,
            user_name=user_name,
            site_name=site_name
        ))
    return result
