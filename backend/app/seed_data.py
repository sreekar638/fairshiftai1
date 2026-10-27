from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app import models
from app.auth import get_password_hash
from app.fatigue_engine import FatigueRuleEngine

def seed_database(db: Session = None):
    close_at_end = False
    if db is None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_at_end = True

    # 1. Create Organizations
    org_construction = models.Organization(
        name="Apex BuildTech Infrastructure",
        industry="construction",
        code="APEX-CONST-01"
    )
    org_college = models.Organization(
        name="St. Jude Metropolitan College",
        industry="education",
        code="STJUDE-EDU-01"
    )
    db.add_all([org_construction, org_college])
    db.commit()
    db.refresh(org_construction)
    db.refresh(org_college)

    # 2. Create Sites and Departments
    site_alpha = models.SiteOrDepartment(
        org_id=org_construction.id,
        name="Tower A - High-Rise Foundation",
        facility_type="site",
        location="Sector 42, Metro Expressway Zone",
        qr_token="QR-APEX-TOWER-A"
    )
    site_beta = models.SiteOrDepartment(
        org_id=org_construction.id,
        name="Pre-Cast Concrete Yard B",
        facility_type="site",
        location="Industrial Corridor West",
        qr_token="QR-APEX-YARD-B"
    )
    dept_science = models.SiteOrDepartment(
        org_id=org_college.id,
        name="Faculty of Science & Chemical Labs",
        facility_type="department",
        location="North Campus Science Complex",
        qr_token="QR-STJUDE-SCI-LAB"
    )
    dept_humanities = models.SiteOrDepartment(
        org_id=org_college.id,
        name="Humanities & Student Services Hall",
        facility_type="department",
        location="Central Campus Building C",
        qr_token="QR-STJUDE-HUMANITIES"
    )
    db.add_all([site_alpha, site_beta, dept_science, dept_humanities])
    db.commit()
    db.refresh(site_alpha)
    db.refresh(site_beta)
    db.refresh(dept_science)
    db.refresh(dept_humanities)

    # 3. Create Demo Users
    hashed_pwd = get_password_hash("Password123!")

    # Global Demo Admin
    demo_admin = models.User(
        org_id=org_construction.id,
        site_id=site_alpha.id,
        email="demo.admin@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Sarah Jenkins (Super Admin)",
        role="admin",
        hourly_rate=35.00,
        worker_code="ADM-001",
        phone="+1 555-0199",
        language_pref="en"
    )

    # Construction Industry Users
    const_admin = models.User(
        org_id=org_construction.id,
        site_id=site_alpha.id,
        email="admin.construction@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Marcus Vance (Site Director)",
        role="admin",
        hourly_rate=32.00,
        worker_code="CST-ADM-01",
        phone="+1 555-0101",
        language_pref="en"
    )
    const_supervisor = models.User(
        org_id=org_construction.id,
        site_id=site_alpha.id,
        email="supervisor.construction@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="David Chen (Rigging Supervisor)",
        role="supervisor",
        hourly_rate=26.50,
        worker_code="CST-SUP-01",
        phone="+1 555-0102",
        language_pref="en"
    )
    const_worker_1 = models.User(
        org_id=org_construction.id,
        site_id=site_alpha.id,
        email="worker.construction@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Ravi Kumar (Tower Crane Specialist)",
        role="worker",
        hourly_rate=21.00,
        worker_code="CST-WRK-01",
        phone="+1 555-0103",
        language_pref="en"
    )
    const_worker_2 = models.User(
        org_id=org_construction.id,
        site_id=site_beta.id,
        email="arun.worker@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Arun Murugan (Concrete Formwork Craftsman)",
        role="worker",
        hourly_rate=19.50,
        worker_code="CST-WRK-02",
        phone="+1 555-0104",
        language_pref="ta"  # Tamil preference
    )

    # College Industry Users
    college_admin = models.User(
        org_id=org_college.id,
        site_id=dept_science.id,
        email="admin.college@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Dr. Eleanor Vance (Dean of Operations)",
        role="admin",
        hourly_rate=38.00,
        worker_code="EDU-ADM-01",
        phone="+1 555-0201",
        language_pref="en"
    )
    college_supervisor = models.User(
        org_id=org_college.id,
        site_id=dept_science.id,
        email="supervisor.college@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Prof. Robert Thorne (Lab Safety Coordinator)",
        role="supervisor",
        hourly_rate=28.00,
        worker_code="EDU-SUP-01",
        phone="+1 555-0202",
        language_pref="en"
    )
    college_worker_1 = models.User(
        org_id=org_college.id,
        site_id=dept_science.id,
        email="worker.college@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Ananya Sharma (Senior Lab Instructor)",
        role="worker",
        hourly_rate=24.00,
        worker_code="EDU-WRK-01",
        phone="+1 555-0203",
        language_pref="en"
    )
    college_worker_2 = models.User(
        org_id=org_college.id,
        site_id=dept_humanities.id,
        email="priya.worker@fairshift.io",
        hashed_password=hashed_pwd,
        full_name="Priya Natarajan (Campus Facility Specialist)",
        role="worker",
        hourly_rate=20.00,
        worker_code="EDU-WRK-02",
        phone="+1 555-0204",
        language_pref="ta"
    )

    db.add_all([
        demo_admin, const_admin, const_supervisor, const_worker_1, const_worker_2,
        college_admin, college_supervisor, college_worker_1, college_worker_2
    ])
    db.commit()
    for u in [demo_admin, const_admin, const_supervisor, const_worker_1, const_worker_2,
              college_admin, college_supervisor, college_worker_1, college_worker_2]:
        db.refresh(u)

    # 4. Create Historical & Active Shifts
    now = datetime.utcnow()

    # Worker 1: Completed shifts over the past 5 days, plus 1 active shift today
    for i in range(5, 0, -1):
        shift_date = now - timedelta(days=i)
        start_time = datetime(shift_date.year, shift_date.month, shift_date.day, 8, 0)
        # On day 2, introduce an extended shift (13.5 hours) to trigger Fatigue Alert!
        hours = 13.5 if i == 2 else 9.0
        end_time = start_time + timedelta(hours=hours)
        reg_hours = min(8.0, hours)
        ot_hours = max(0.0, hours - 8.0)

        s = models.Shift(
            org_id=org_construction.id,
            user_id=const_worker_1.id,
            site_id=site_alpha.id,
            scheduled_start=start_time,
            scheduled_end=start_time + timedelta(hours=8),
            actual_check_in=start_time,
            actual_check_out=end_time,
            regular_hours=reg_hours,
            overtime_hours=ot_hours,
            status="completed",
            notes=f"Reinforcement pour zone 4 - day {6-i}"
        )
        db.add(s)
        db.commit()
        db.refresh(s)

        # Run Fatigue Engine on historical shifts
        FatigueRuleEngine.evaluate_shift(db, s)

    # Active shift today for const_worker_1
    active_shift_start = datetime(now.year, now.month, now.day, 7, 30)
    active_shift_1 = models.Shift(
        org_id=org_construction.id,
        user_id=const_worker_1.id,
        site_id=site_alpha.id,
        scheduled_start=active_shift_start,
        scheduled_end=active_shift_start + timedelta(hours=8),
        actual_check_in=active_shift_start,
        actual_check_out=None,
        regular_hours=0.0,
        overtime_hours=0.0,
        status="in_progress",
        notes="Active crane inspection and pre-lift briefing."
    )
    db.add(active_shift_1)
    db.commit()

    # Attendance event for check-in
    ev1 = models.AttendanceEvent(
        shift_id=active_shift_1.id,
        user_id=const_worker_1.id,
        event_type="check_in",
        timestamp=active_shift_start,
        method="qr",
        latitude=13.0827,
        longitude=80.2707,
        notes="QR Scan at Tower A Gate 1"
    )
    db.add(ev1)

    # College worker shifts
    for i in range(4, 0, -1):
        shift_date = now - timedelta(days=i)
        start_time = datetime(shift_date.year, shift_date.month, shift_date.day, 9, 0)
        end_time = start_time + timedelta(hours=8.5)
        s_edu = models.Shift(
            org_id=org_college.id,
            user_id=college_worker_1.id,
            site_id=dept_science.id,
            scheduled_start=start_time,
            scheduled_end=start_time + timedelta(hours=8),
            actual_check_in=start_time,
            actual_check_out=end_time,
            regular_hours=8.0,
            overtime_hours=0.5,
            status="completed",
            notes="Organic Chemistry Lab practical sessions and chemical inventory"
        )
        db.add(s_edu)
        db.commit()
        db.refresh(s_edu)
        FatigueRuleEngine.evaluate_shift(db, s_edu)

    # Active shift for college worker
    active_edu_start = datetime(now.year, now.month, now.day, 8, 45)
    active_shift_2 = models.Shift(
        org_id=org_college.id,
        user_id=college_worker_1.id,
        site_id=dept_science.id,
        scheduled_start=active_edu_start,
        scheduled_end=active_edu_start + timedelta(hours=8),
        actual_check_in=active_edu_start,
        actual_check_out=None,
        regular_hours=0.0,
        overtime_hours=0.0,
        status="in_progress",
        notes="Advanced Physics Optics Lab preparation"
    )
    db.add(active_shift_2)
    db.commit()

    # 5. Create Synthetic Payslips
    # Payslip 1 for const_worker_1
    ps1 = models.Payslip(
        org_id=org_construction.id,
        user_id=const_worker_1.id,
        period_start=now - timedelta(days=21),
        period_end=now - timedelta(days=7),
        base_hourly_rate=21.00,
        regular_hours=80.0,
        overtime_hours=14.5,
        overtime_rate=1.5,
        allowances=120.00,  # Safety gear & transport allowance
        deductions=145.50,  # Insurance and statutory welfare
        gross_pay=(80.0 * 21.00) + (14.5 * 21.00 * 1.5) + 120.00,
        net_pay=((80.0 * 21.00) + (14.5 * 21.00 * 1.5) + 120.00) - 145.50,
        status="approved"
    )

    # Payslip 2 for college_worker_1
    ps2 = models.Payslip(
        org_id=org_college.id,
        user_id=college_worker_1.id,
        period_start=now - timedelta(days=21),
        period_end=now - timedelta(days=7),
        base_hourly_rate=24.00,
        regular_hours=75.0,
        overtime_hours=6.0,
        overtime_rate=1.5,
        allowances=95.00,
        deductions=110.00,
        gross_pay=(75.0 * 24.00) + (6.0 * 24.00 * 1.5) + 95.00,
        net_pay=((75.0 * 24.00) + (6.0 * 24.00 * 1.5) + 95.00) - 110.00,
        status="paid"
    )
    db.add_all([ps1, ps2])
    db.commit()

    # 6. Create Safety and Workplace Reports
    rep1 = models.SafetyReport(
        ref_number="SAF-2026-081",
        org_id=org_construction.id,
        user_id=const_worker_1.id,
        site_id=site_alpha.id,
        category="hazard",
        title="Unsecured Perimeter Guardrail on 14th Floor Slab",
        description="The safety toe-board and wire rope perimeter railing on the east edge of floor 14 are loose after wind gusts.",
        priority="critical",
        is_anonymous=False,
        status="investigating",
        resolution_notes="Safety officer Marcus dispatched scaffolding team for immediate tie-off and re-anchoring.",
        reported_at=now - timedelta(hours=18)
    )
    rep2 = models.SafetyReport(
        ref_number="SAF-2026-082",
        org_id=org_construction.id,
        user_id=None,  # Anonymous report!
        site_id=site_beta.id,
        category="equipment",
        title="Forklift Hydraulic Fluid Leak Near Pedestrian Walkway",
        description="Forklift FL-04 has a steady oil leak near the main material staging zone causing severe slip hazard.",
        priority="high",
        is_anonymous=True,
        status="reported",
        resolution_notes=None,
        reported_at=now - timedelta(hours=6)
    )
    rep3 = models.SafetyReport(
        ref_number="EDU-2026-014",
        org_id=org_college.id,
        user_id=college_worker_1.id,
        site_id=dept_science.id,
        category="maintenance",
        title="Fume Hood Exhaust Inefficiency in Organic Lab 302",
        description="Air velocity monitor indicates below safe CFM threshold. Solvents cannot be safely boiled during students' afternoon lab.",
        priority="high",
        is_anonymous=False,
        status="resolved",
        resolution_notes="Facilities HVAC team cleared the blocked damper on the rooftop extraction unit. Recertified safe at 102 fpm airflow.",
        reported_at=now - timedelta(days=2),
        resolved_at=now - timedelta(days=1)
    )
    db.add_all([rep1, rep2, rep3])
    db.commit()
    db.refresh(rep1)
    db.refresh(rep2)
    db.refresh(rep3)

    # Report Action Logs
    log1 = models.ReportActionLog(
        report_id=rep1.id,
        actor_id=const_admin.id,
        action="Status changed to investigating",
        notes="Site safety team notified. Work halted on east edge pending inspection."
    )
    log2 = models.ReportActionLog(
        report_id=rep3.id,
        actor_id=college_admin.id,
        action="Status changed to resolved",
        notes="HVAC filter replaced and airflow recertified."
    )
    db.add_all([log1, log2])
    db.commit()

    # 7. Create Honest Anonymous Feedback
    fb1 = models.Feedback(
        org_id=org_construction.id,
        site_id=site_alpha.id,
        condition_rating=4,
        workload_rating=3,
        break_rating=2,  # highlights break facility need
        facility_rating=3,
        supervisor_rating=4,
        comments="Adequate safety gear provided, but afternoon shade and cool drinking water refilling stations need improvement on upper floors.",
        is_anonymous=True,
        created_at=now - timedelta(days=2)
    )
    fb2 = models.Feedback(
        org_id=org_construction.id,
        site_id=site_beta.id,
        condition_rating=4,
        workload_rating=4,
        break_rating=4,
        facility_rating=4,
        supervisor_rating=5,
        comments="Clear shift timings this week. Supervisor David ensured timely pre-shift tool talks.",
        is_anonymous=True,
        created_at=now - timedelta(days=3)
    )
    fb3 = models.Feedback(
        org_id=org_college.id,
        site_id=dept_science.id,
        condition_rating=4,
        workload_rating=3,
        break_rating=4,
        facility_rating=4,
        supervisor_rating=4,
        comments="Lab schedules are consistent. Requesting digital chemical inventory logger to reduce manual documentation time.",
        is_anonymous=True,
        created_at=now - timedelta(days=1)
    )
    db.add_all([fb1, fb2, fb3])
    db.commit()

    # 8. Create Skill Passport Entries
    sk1 = models.SkillPassport(
        org_id=org_construction.id,
        user_id=const_worker_1.id,
        title="Heavy Tower Crane Operator Certification (Class A)",
        category="machinery",
        issuer="National Heavy Machinery Safety Board",
        issue_date=now - timedelta(days=300),
        expiry_date=now + timedelta(days=430),
        is_verified=True,
        verified_by="Marcus Vance (Site Director)",
        verification_notes="Verified against official registry database #CRN-9981.",
        document_ref="doc_crane_cert_9981.pdf"
    )
    sk2 = models.SkillPassport(
        org_id=org_construction.id,
        user_id=const_worker_1.id,
        title="OSHA 30-Hour Construction Safety & Fall Protection",
        category="safety",
        issuer="Occupational Safety Council",
        issue_date=now - timedelta(days=150),
        expiry_date=now + timedelta(days=580),
        is_verified=True,
        verified_by="Marcus Vance (Site Director)",
        verification_notes="Completed 30-hour intensive course.",
        document_ref="doc_osha30_ravi.pdf"
    )
    sk3 = models.SkillPassport(
        org_id=org_construction.id,
        user_id=const_worker_2.id,
        title="Advanced Hydraulic Rebar Bending & Formwork",
        category="technical",
        issuer="Vocational Apprenticeship Council",
        issue_date=now - timedelta(days=90),
        expiry_date=None,
        is_verified=False,  # Self-declared pending verification
        verified_by=None,
        verification_notes="Self-submitted certificate pending site supervisor audit.",
        document_ref="doc_rebar_arun.pdf"
    )
    sk4 = models.SkillPassport(
        org_id=org_college.id,
        user_id=college_worker_1.id,
        title="Hazardous Materials Storage & Chemical Spill Response",
        category="safety",
        issuer="University Environmental Health & Safety Division",
        issue_date=now - timedelta(days=180),
        expiry_date=now + timedelta(days=185),
        is_verified=True,
        verified_by="Prof. Robert Thorne",
        verification_notes="Annual laboratory safety protocol refresher passed.",
        document_ref="doc_chem_spill_cert.pdf"
    )
    db.add_all([sk1, sk2, sk3, sk4])
    db.commit()

    if close_at_end:
        db.close()

if __name__ == "__main__":
    seed_database()
    print("FairShift AI database initialized and seeded successfully.")
