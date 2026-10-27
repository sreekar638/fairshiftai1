from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/skills", tags=["Skill Passport"])

def format_skill_read(sk: models.SkillPassport) -> schemas.SkillRead if hasattr(schemas, 'SkillRead') else schemas.SkillPassportRead:
    return schemas.SkillPassportRead(
        id=sk.id,
        org_id=sk.org_id,
        user_id=sk.user_id,
        title=sk.title,
        category=sk.category,
        issuer=sk.issuer,
        issue_date=sk.issue_date,
        expiry_date=sk.expiry_date,
        is_verified=sk.is_verified,
        verified_by=sk.verified_by,
        verification_notes=sk.verification_notes,
        created_at=sk.created_at,
        user_name=sk.user.full_name if sk.user else None
    )

@router.get("/my-skills", response_model=List[schemas.SkillPassportRead])
def get_my_skills(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skills = db.query(models.SkillPassport).filter(
        models.SkillPassport.user_id == current_user.id
    ).order_by(models.SkillPassport.issue_date.desc()).all()
    return [format_skill_read(s) for s in skills]

@router.post("", response_model=schemas.SkillPassportRead)
def add_skill(
    payload: schemas.SkillPassportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skill = models.SkillPassport(
        org_id=current_user.org_id,
        user_id=current_user.id,
        title=payload.title,
        category=payload.category,
        issuer=payload.issuer,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        is_verified=False,  # Newly self-declared
        document_ref=payload.document_ref
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return format_skill_read(skill)

@router.get("/all", response_model=List[schemas.SkillPassportRead])
def get_all_skills_admin(
    verified_only: Optional[bool] = None,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    query = db.query(models.SkillPassport).filter(
        models.SkillPassport.org_id == current_user.org_id
    )
    if verified_only is not None:
        query = query.filter(models.SkillPassport.is_verified == verified_only)

    skills = query.order_by(models.SkillPassport.created_at.desc()).all()
    return [format_skill_read(s) for s in skills]

@router.patch("/{skill_id}/verify", response_model=schemas.SkillPassportRead)
def verify_skill(
    skill_id: int,
    payload: schemas.SkillPassportVerify,
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    skill = db.query(models.SkillPassport).filter(
        models.SkillPassport.id == skill_id,
        models.SkillPassport.org_id == current_user.org_id
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill passport entry not found")

    skill.is_verified = payload.is_verified
    skill.verified_by = current_user.full_name if payload.is_verified else None
    skill.verification_notes = payload.verification_notes
    db.commit()
    db.refresh(skill)
    return format_skill_read(skill)
