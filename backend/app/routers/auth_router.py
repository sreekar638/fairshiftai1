from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def format_user_read(user: models.User, db: Session) -> schemas.UserRead:
    org = db.query(models.Organization).filter(models.Organization.id == user.org_id).first()
    site = db.query(models.SiteOrDepartment).filter(models.SiteOrDepartment.id == user.site_id).first() if user.site_id else None
    return schemas.UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hourly_rate=user.hourly_rate,
        worker_code=user.worker_code,
        phone=user.phone,
        language_pref=user.language_pref,
        site_id=user.site_id,
        org_id=user.org_id,
        created_at=user.created_at,
        organization_name=org.name if org else "Unknown Organization",
        organization_industry=org.industry if org else "general",
        site_name=site.name if site else None
    )

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "org_id": user.org_id})
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=format_user_read(user, db)
    )

@router.post("/login", response_model=schemas.Token)
def login_json(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "org_id": user.org_id})
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=format_user_read(user, db)
    )

@router.get("/me", response_model=schemas.UserRead)
def read_current_user_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return format_user_read(current_user, db)

@router.get("/demo-users")
def get_demo_users(db: Session = Depends(get_db)):
    """Convenience helper for judges and hackathon testers to switch personas with one click."""
    users = db.query(models.User).all()
    results = []
    for u in users:
        org = db.query(models.Organization).filter(models.Organization.id == u.org_id).first()
        results.append({
            "id": u.id,
            "email": u.email,
            "name": u.full_name,
            "role": u.role,
            "industry": org.industry if org else "general",
            "org_name": org.name if org else "Org",
            "worker_code": u.worker_code,
            "language": u.language_pref
        })
    return results

@router.post("/switch-demo/{user_id}", response_model=schemas.Token)
def switch_demo_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Demo user not found")
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "org_id": user.org_id})
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=format_user_read(user, db)
    )
