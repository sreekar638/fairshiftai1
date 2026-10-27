from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/feedback", tags=["Honest Workplace Feedback"])

@router.post("", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: schemas.FeedbackCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedback = models.Feedback(
        org_id=current_user.org_id,
        site_id=payload.site_id or current_user.site_id,
        condition_rating=payload.condition_rating,
        workload_rating=payload.workload_rating,
        break_rating=payload.break_rating,
        facility_rating=payload.facility_rating,
        supervisor_rating=payload.supervisor_rating,
        comments=payload.comments,
        is_anonymous=payload.is_anonymous
    )
    db.add(feedback)
    db.commit()
    return {"message": "Thank you. Your feedback has been recorded anonymously and protected."}

@router.get("/aggregate", response_model=schemas.FeedbackAggregate)
def get_aggregate_feedback(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedbacks = db.query(models.Feedback).filter(
        models.Feedback.org_id == current_user.org_id
    ).all()

    if not feedbacks:
        return schemas.FeedbackAggregate(
            total_responses=0,
            avg_condition=5.0,
            avg_workload=5.0,
            avg_breaks=5.0,
            avg_facilities=5.0,
            avg_supervisor=5.0,
            recent_comments=[]
        )

    count = len(feedbacks)
    avg_c = round(sum(f.condition_rating for f in feedbacks) / count, 1)
    avg_w = round(sum(f.workload_rating for f in feedbacks) / count, 1)
    avg_b = round(sum(f.break_rating for f in feedbacks) / count, 1)
    avg_f = round(sum(f.facility_rating for f in feedbacks) / count, 1)
    avg_s = round(sum(f.supervisor_rating for f in feedbacks) / count, 1)

    comments = [f.comments for f in feedbacks if f.comments]

    return schemas.FeedbackAggregate(
        total_responses=count,
        avg_condition=avg_c,
        avg_workload=avg_w,
        avg_breaks=avg_b,
        avg_facilities=avg_f,
        avg_supervisor=avg_s,
        recent_comments=comments[:10]
    )
