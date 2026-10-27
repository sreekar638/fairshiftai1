from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app import models

class FatigueRuleEngine:
    """
    Transparent, configurable rule-based engine for occupational fatigue risk detection.
    Evaluates:
      1. Excessive single shift duration (> 10h warning, > 12h critical)
      2. Insufficient rest between consecutive shifts (< 10h warning, < 8h critical)
      3. Consecutive working days (> 6 days warning, > 10 days critical)
    Does not diagnose medical conditions; provides objective operational safety suggestions.
    """

    @classmethod
    def evaluate_shift(cls, db: Session, shift: models.Shift) -> List[models.FatigueAlert]:
        alerts_generated = []
        if not shift.actual_check_in or not shift.actual_check_out:
            return alerts_generated

        # 1. Evaluate Single Shift Duration
        duration_hours = (shift.actual_check_out - shift.actual_check_in).total_seconds() / 3600.0

        if duration_hours >= 12.0:
            existing = db.query(models.FatigueAlert).filter(
                models.FatigueAlert.shift_id == shift.id,
                models.FatigueAlert.rule_code == "EXCESSIVE_HOURS_CRITICAL"
            ).first()
            if not existing:
                alert = models.FatigueAlert(
                    org_id=shift.org_id,
                    user_id=shift.user_id,
                    shift_id=shift.id,
                    rule_code="EXCESSIVE_HOURS_CRITICAL",
                    severity="critical",
                    title="Critical Shift Duration Exceeded",
                    details=f"Shift duration was {duration_hours:.1f} hours (exceeded mandatory 12.0 hour safety threshold).",
                    suggested_action="Mandate minimum 12-hour recovery rest before next scheduled dispatch. Review workload allocation.",
                    status="active"
                )
                db.add(alert)
                alerts_generated.append(alert)
        elif duration_hours >= 10.0:
            existing = db.query(models.FatigueAlert).filter(
                models.FatigueAlert.shift_id == shift.id,
                models.FatigueAlert.rule_code == "EXCESSIVE_HOURS_WARNING"
            ).first()
            if not existing:
                alert = models.FatigueAlert(
                    org_id=shift.org_id,
                    user_id=shift.user_id,
                    shift_id=shift.id,
                    rule_code="EXCESSIVE_HOURS_WARNING",
                    severity="warning",
                    title="Extended Shift Warning",
                    details=f"Shift duration reached {duration_hours:.1f} hours (exceeded standard 10.0 hour limit).",
                    suggested_action="Ensure adequate hydration and scheduled fatigue recovery pauses.",
                    status="active"
                )
                db.add(alert)
                alerts_generated.append(alert)

        # 2. Evaluate Rest Interval from Previous Completed Shift
        previous_shift = db.query(models.Shift).filter(
            models.Shift.user_id == shift.user_id,
            models.Shift.id != shift.id,
            models.Shift.actual_check_out.isnot(None),
            models.Shift.actual_check_out <= shift.actual_check_in
        ).order_by(models.Shift.actual_check_out.desc()).first()

        if previous_shift and previous_shift.actual_check_out:
            rest_hours = (shift.actual_check_in - previous_shift.actual_check_out).total_seconds() / 3600.0
            if rest_hours < 8.0:
                existing = db.query(models.FatigueAlert).filter(
                    models.FatigueAlert.shift_id == shift.id,
                    models.FatigueAlert.rule_code == "SHORT_REST_CRITICAL"
                ).first()
                if not existing:
                    alert = models.FatigueAlert(
                        org_id=shift.org_id,
                        user_id=shift.user_id,
                        shift_id=shift.id,
                        rule_code="SHORT_REST_CRITICAL",
                        severity="critical",
                        title="Critical Turnaround Rest Deficit",
                        details=f"Only {rest_hours:.1f} hours recorded rest between consecutive shifts (minimum required: 8.0 hours).",
                        suggested_action="Supervisor intervention recommended: reassign safety-sensitive tasks and schedule rest pause.",
                        status="active"
                    )
                    db.add(alert)
                    alerts_generated.append(alert)
            elif rest_hours < 10.0:
                existing = db.query(models.FatigueAlert).filter(
                    models.FatigueAlert.shift_id == shift.id,
                    models.FatigueAlert.rule_code == "SHORT_REST_WARNING"
                ).first()
                if not existing:
                    alert = models.FatigueAlert(
                        org_id=shift.org_id,
                        user_id=shift.user_id,
                        shift_id=shift.id,
                        rule_code="SHORT_REST_WARNING",
                        severity="warning",
                        title="Sub-optimal Turnaround Rest",
                        details=f"Rest interval was {rest_hours:.1f} hours (below recommended 10.0 hour threshold).",
                        suggested_action="Monitor worker for early fatigue signs and ensure non-hazardous task assignment.",
                        status="active"
                    )
                    db.add(alert)
                    alerts_generated.append(alert)

        # 3. Evaluate Consecutive Working Days
        # Look back 14 days
        cutoff_date = shift.actual_check_in.date() - timedelta(days=14)
        past_shifts = db.query(models.Shift).filter(
            models.Shift.user_id == shift.user_id,
            models.Shift.actual_check_in.isnot(None),
            models.Shift.actual_check_in >= datetime.combine(cutoff_date, datetime.min.time())
        ).order_by(models.Shift.actual_check_in.desc()).all()

        distinct_days = set()
        for s in past_shifts:
            if s.actual_check_in:
                distinct_days.add(s.actual_check_in.date())

        # Count consecutive days ending on current shift date
        consecutive_count = 0
        current_check_day = shift.actual_check_in.date()
        while current_check_day in distinct_days:
            consecutive_count += 1
            current_check_day -= timedelta(days=1)

        if consecutive_count >= 7:
            existing = db.query(models.FatigueAlert).filter(
                models.FatigueAlert.user_id == shift.user_id,
                models.FatigueAlert.rule_code == "CONSECUTIVE_DAYS_LIMIT",
                models.FatigueAlert.created_at >= datetime.utcnow() - timedelta(days=1)
            ).first()
            if not existing:
                severity = "critical" if consecutive_count >= 10 else "warning"
                alert = models.FatigueAlert(
                    org_id=shift.org_id,
                    user_id=shift.user_id,
                    shift_id=shift.id,
                    rule_code="CONSECUTIVE_DAYS_LIMIT",
                    severity=severity,
                    title=f"Consecutive Days Risk ({consecutive_count} Days)",
                    details=f"Worker has logged shifts for {consecutive_count} consecutive calendar days without a full 24-hour rest cycle.",
                    suggested_action="Mandate consecutive 24-48 hour rest day in upcoming roster schedule per SDG 8 safety guidelines.",
                    status="active"
                )
                db.add(alert)
                alerts_generated.append(alert)

        db.commit()
        return alerts_generated
