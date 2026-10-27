from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/payslips", tags=["Payslips"])

def to_payslip_read(p: models.Payslip) -> schemas.PayslipRead:
    return schemas.PayslipRead(
        id=p.id,
        org_id=p.org_id,
        user_id=p.user_id,
        period_start=p.period_start,
        period_end=p.period_end,
        base_hourly_rate=p.base_hourly_rate,
        regular_hours=p.regular_hours,
        overtime_hours=p.overtime_hours,
        overtime_rate=p.overtime_rate,
        allowances=p.allowances,
        deductions=p.deductions,
        gross_pay=p.gross_pay,
        net_pay=p.net_pay,
        status=p.status,
        synthetic_disclaimer=p.synthetic_disclaimer,
        created_at=p.created_at,
        user_name=p.user.full_name if p.user else None
    )

@router.get("/my-payslips", response_model=List[schemas.PayslipRead])
def get_my_payslips(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payslips = db.query(models.Payslip).filter(
        models.Payslip.user_id == current_user.id
    ).order_by(models.Payslip.period_end.desc()).all()
    return [to_payslip_read(p) for p in payslips]

@router.get("/{payslip_id}", response_model=schemas.PayslipRead)
def get_payslip_by_id(
    payslip_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payslip = db.query(models.Payslip).filter(models.Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")

    # Access check: worker can only see their own payslip; admin can see within org
    if current_user.role == "worker" and payslip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot view another worker's payslip")
    if payslip.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Forbidden: Organization mismatch")

    return to_payslip_read(payslip)

@router.post("/generate", response_model=schemas.PayslipRead)
def generate_payslip(
    payload: schemas.PayslipGenerateRequest,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    target_user = db.query(models.User).filter(
        models.User.id == payload.user_id,
        models.User.org_id == current_user.org_id
    ).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target worker not found in organization")

    # Aggregate completed shifts in period
    shifts = db.query(models.Shift).filter(
        models.Shift.user_id == target_user.id,
        models.Shift.scheduled_start >= payload.period_start,
        models.Shift.scheduled_start <= payload.period_end,
        models.Shift.status == "completed"
    ).all()

    total_reg = sum(s.regular_hours for s in shifts)
    total_ot = sum(s.overtime_hours for s in shifts)

    base_rate = target_user.hourly_rate or 18.50
    ot_multiplier = 1.5

    # Demonstrative allowances & deductions policy
    allowances = round(total_reg * 1.25, 2)  # Demo: standard shift attendance allowance
    gross_pay = round((total_reg * base_rate) + (total_ot * base_rate * ot_multiplier) + allowances, 2)
    deductions = round(gross_pay * 0.08, 2)  # Demo: statutory welfare & insurance deduction
    net_pay = round(gross_pay - deductions, 2)

    payslip = models.Payslip(
        org_id=current_user.org_id,
        user_id=target_user.id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        base_hourly_rate=base_rate,
        regular_hours=total_reg,
        overtime_hours=total_ot,
        overtime_rate=ot_multiplier,
        allowances=allowances,
        deductions=deductions,
        gross_pay=gross_pay,
        net_pay=net_pay,
        status="generated"
    )
    db.add(payslip)
    db.commit()
    db.refresh(payslip)
    return to_payslip_read(payslip)
