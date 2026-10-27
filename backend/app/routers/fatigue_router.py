from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/fatigue", tags=["Fatigue Risk Engine"])

def format_alert_read(alert: models.FatigueAlert) -> schemas.FatigueAlertRead:
    return schemas.FatigueAlertRead(
        id=alert.id,
        org_id=alert.org_id,
        user_id=alert.user_id,
        shift_id=alert.shift_id,
        rule_code=alert.rule_code,
        severity=alert.severity,
        title=alert.title,
        details=alert.details,
        suggested_action=alert.suggested_action,
        status=alert.status,
        created_at=alert.created_at,
        user_name=alert.user.full_name if alert.user else None
    )

@router.get("/my-alerts", response_model=List[schemas.FatigueAlertRead])
def get_my_alerts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alerts = db.query(models.FatigueAlert).filter(
        models.FatigueAlert.user_id == current_user.id
    ).order_by(models.FatigueAlert.created_at.desc()).all()
    return [format_alert_read(a) for a in alerts]

@router.get("/active", response_model=List[schemas.FatigueAlertRead])
def get_active_alerts_admin(
    severity: Optional[str] = None,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    query = db.query(models.FatigueAlert).filter(
        models.FatigueAlert.org_id == current_user.org_id
    )
    if severity:
        query = query.filter(models.FatigueAlert.severity == severity)

    alerts = query.order_by(models.FatigueAlert.created_at.desc()).all()
    return [format_alert_read(a) for a in alerts]

@router.patch("/{alert_id}/acknowledge", response_model=schemas.FatigueAlertRead)
def acknowledge_alert(
    alert_id: int,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    alert = db.query(models.FatigueAlert).filter(
        models.FatigueAlert.id == alert_id,
        models.FatigueAlert.org_id == current_user.org_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Fatigue alert not found")

    alert.status = "acknowledged"
    db.commit()
    db.refresh(alert)
    return format_alert_read(alert)
