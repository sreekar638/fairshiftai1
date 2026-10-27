import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas

class AIInsightsEngine:
    @classmethod
    def generate_recommendations(cls, db: Session, org_id: int) -> List[schemas.AIRecommendation]:
        recommendations: List[schemas.AIRecommendation] = []

        # 1. Inspect Overtime Ratio
        shifts = db.query(models.Shift).filter(
            models.Shift.org_id == org_id,
            models.Shift.status == "completed"
        ).all()
        total_reg = sum(s.regular_hours for s in shifts)
        total_ot = sum(s.overtime_hours for s in shifts)
        ot_ratio = (total_ot / total_reg) if total_reg > 0 else 0.0

        if ot_ratio > 0.20:
            recommendations.append(schemas.AIRecommendation(
                category="Overtime & Workload",
                title="Excessive Overtime Strain Detected",
                observation=f"Overtime accounts for {ot_ratio*100:.1f}% of all logged hours, exceeding the 20% sustainable threshold.",
                evidence_metric=f"{total_ot:.1f} OT hours logged against {total_reg:.1f} regular hours.",
                recommended_action="Review shift staffing allocations and consider adding relief roster capacity to mitigate burnout.",
                confidence=0.92,
                source="deterministic_rule"
            ))
        elif ot_ratio > 0.10:
            recommendations.append(schemas.AIRecommendation(
                category="Overtime & Workload",
                title="Moderate Overtime Pattern",
                observation=f"Overtime ratio is at {ot_ratio*100:.1f}%. Stable but requires proactive tracking.",
                evidence_metric=f"{total_ot:.1f} hours of overtime recorded across recent rosters.",
                recommended_action="Ensure overtime distribution is equitable among qualified team members.",
                confidence=0.88,
                source="deterministic_rule"
            ))

        # 2. Inspect Safety Hazard Trends
        unresolved_reports = db.query(models.SafetyReport).filter(
            models.SafetyReport.org_id == org_id,
            models.SafetyReport.status.in_(["reported", "investigating"])
        ).all()

        critical_hazards = [r for r in unresolved_reports if r.priority in ["critical", "high"]]
        if len(critical_hazards) > 0:
            recommendations.append(schemas.AIRecommendation(
                category="Safety & Compliance",
                title="Immediate Safety Hazard Intervention Required",
                observation=f"{len(critical_hazards)} high/critical priority workplace reports remain active without final resolution.",
                evidence_metric=f"Unresolved critical cases: {', '.join([r.ref_number for r in critical_hazards[:3]])}",
                recommended_action="Dispatch designated safety supervisor to inspect the reported facilities immediately.",
                confidence=0.96,
                source="deterministic_rule"
            ))

        # 3. Inspect Fatigue Alerts
        active_alerts = db.query(models.FatigueAlert).filter(
            models.FatigueAlert.org_id == org_id,
            models.FatigueAlert.status == "active"
        ).count()
        if active_alerts > 0:
            recommendations.append(schemas.AIRecommendation(
                category="Worker Well-being (SDG 8.8)",
                title="Active Fatigue Alerts in Roster",
                observation=f"{active_alerts} worker fatigue risk triggers currently active due to long shifts or insufficient rest periods.",
                evidence_metric=f"{active_alerts} safety rules triggered in current scheduling cycle.",
                recommended_action="Mandate minimum turnaround rest intervals and avoid back-to-back double shifts.",
                confidence=0.95,
                source="deterministic_rule"
            ))

        # 4. Inspect Skill Verification Gaps
        total_skills = db.query(models.SkillPassport).filter(
            models.SkillPassport.org_id == org_id
        ).count()
        verified_skills = db.query(models.SkillPassport).filter(
            models.SkillPassport.org_id == org_id,
            models.SkillPassport.is_verified == True
        ).count()

        if total_skills > 0:
            verification_rate = (verified_skills / total_skills) * 100
            if verification_rate < 70.0:
                recommendations.append(schemas.AIRecommendation(
                    category="Skill Passport & Verification",
                    title="Skill Verification Backlog",
                    observation=f"Only {verification_rate:.1f}% of recorded employee qualifications have been supervisor-verified.",
                    evidence_metric=f"{total_skills - verified_skills} pending qualification reviews.",
                    recommended_action="Audit self-declared certifications (e.g. OSHA safety, heavy machinery, pedagogical compliance).",
                    confidence=0.85,
                    source="deterministic_rule"
                ))

        # 5. Inspect Anonymous Feedback
        feedbacks = db.query(models.Feedback).filter(
            models.Feedback.org_id == org_id
        ).all()
        if feedbacks:
            avg_break = sum(f.break_rating for f in feedbacks) / len(feedbacks)
            if avg_break < 3.0:
                recommendations.append(schemas.AIRecommendation(
                    category="Working Conditions (SDG 8.5)",
                    title="Break Facility & Rest Interval Feedback Deficit",
                    observation=f"Workers rated break facilities and rest quality at {avg_break:.1f}/5.0 (below acceptable threshold).",
                    evidence_metric=f"Aggregated from {len(feedbacks)} anonymous feedback submissions.",
                    recommended_action="Inspect designated rest areas, drinking water access, and scheduled rest timings.",
                    confidence=0.90,
                    source="deterministic_rule"
                ))

        return recommendations
