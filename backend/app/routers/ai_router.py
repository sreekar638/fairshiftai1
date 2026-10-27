from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import require_roles
from app.ai_insights import AIInsightsEngine

router = APIRouter(prefix="/ai", tags=["AI Workforce Insights"])

@router.get("/recommendations", response_model=List[schemas.AIRecommendation])
def get_ai_recommendations(
    current_user: models.User = Depends(require_roles(["admin", "supervisor"])),
    db: Session = Depends(get_db)
):
    recommendations = AIInsightsEngine.generate_recommendations(db, current_user.org_id)
    return recommendations
