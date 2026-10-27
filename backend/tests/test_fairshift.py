import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.seed_data import seed_database
from app import models
from app.fatigue_engine import FatigueRuleEngine

# Use an in-memory SQLite database for isolated automated testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "SDG 8" in response.json()["sdg_target"]

def test_authentication_success_and_failure(client):
    # Successful login
    res = client.post("/api/v1/auth/login", json={
        "email": "worker.construction@fairshift.io",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "worker"
    assert data["user"]["organization_industry"] == "construction"

    # Failed login with bad password
    bad_res = client.post("/api/v1/auth/login", json={
        "email": "worker.construction@fairshift.io",
        "password": "WrongPassword!"
    })
    assert bad_res.status_code == 401

def test_role_based_access_control(client):
    # Worker token
    worker_res = client.post("/api/v1/auth/login", json={
        "email": "worker.construction@fairshift.io",
        "password": "Password123!"
    })
    worker_token = worker_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {worker_token}"}

    # Worker trying to access admin dashboard should be forbidden (403)
    dash_res = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert dash_res.status_code == 403

    # Admin login
    admin_res = client.post("/api/v1/auth/login", json={
        "email": "admin.construction@fairshift.io",
        "password": "Password123!"
    })
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin should succeed
    admin_dash_res = client.get("/api/v1/analytics/dashboard", headers=admin_headers)
    assert admin_dash_res.status_code == 200
    assert admin_dash_res.json()["total_workers"] >= 2

def test_shift_checkin_checkout_workflow(client):
    # Login as Arun (construction worker 2)
    res = client.post("/api/v1/auth/login", json={
        "email": "arun.worker@fairshift.io",
        "password": "Password123!"
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Check in with QR code
    check_in_res = client.post("/api/v1/attendance/check-in", json={
        "method": "qr",
        "qr_token": "QR-APEX-YARD-B",
        "notes": "Arrived on site via transport shuttle"
    }, headers=headers)
    assert check_in_res.status_code == 200
    shift_data = check_in_res.json()
    assert shift_data["status"] == "in_progress"

    # Duplicate check-in attempt must fail
    dup_res = client.post("/api/v1/attendance/check-in", json={
        "method": "manual"
    }, headers=headers)
    assert dup_res.status_code == 400

    # Check out
    check_out_res = client.post("/api/v1/attendance/check-out", json={
        "method": "manual",
        "notes": "Completed slab preparation"
    }, headers=headers)
    assert check_out_res.status_code == 200
    assert check_out_res.json()["status"] == "completed"

def test_safety_reporting_anonymous_and_resolution(client):
    # Worker submits anonymous safety hazard
    res = client.post("/api/v1/auth/login", json={
        "email": "worker.construction@fairshift.io",
        "password": "Password123!"
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    report_res = client.post("/api/v1/reports", json={
        "category": "hazard",
        "title": "Damaged Scaffolding Clamps on North Elevation",
        "description": "Cross-brace coupler is cracked and wobbling.",
        "priority": "critical",
        "is_anonymous": True
    }, headers=headers)
    assert report_res.status_code == 200
    rep_data = report_res.json()
    assert rep_data["is_anonymous"] is True
    assert rep_data["reporter_name"] == "Anonymous Worker"
    report_id = rep_data["id"]

    # Admin reviews and resolves report
    admin_res = client.post("/api/v1/auth/login", json={
        "email": "admin.construction@fairshift.io",
        "password": "Password123!"
    })
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    patch_res = client.patch(f"/api/v1/reports/{report_id}/status", json={
        "status": "resolved",
        "resolution_notes": "Scaffolding team replaced cracked clamps with certified heavy-duty couplers."
    }, headers=admin_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "resolved"

def test_fatigue_rule_engine_boundary_conditions():
    db = TestingSessionLocal()
    # Test shift > 12.0 hours
    start = datetime(2026, 10, 1, 6, 0)
    end = start + timedelta(hours=13.0)  # 13 hours
    test_shift = models.Shift(
        org_id=1,
        user_id=1,
        scheduled_start=start,
        scheduled_end=start + timedelta(hours=8),
        actual_check_in=start,
        actual_check_out=end,
        regular_hours=8.0,
        overtime_hours=5.0,
        status="completed"
    )
    db.add(test_shift)
    db.commit()
    db.refresh(test_shift)

    alerts = FatigueRuleEngine.evaluate_shift(db, test_shift)
    critical_alerts = [a for a in alerts if a.rule_code == "EXCESSIVE_HOURS_CRITICAL"]
    assert len(critical_alerts) >= 1
    assert critical_alerts[0].severity == "critical"
    db.close()

def test_payslip_calculation_and_isolation(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "worker.construction@fairshift.io",
        "password": "Password123!"
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payslips_res = client.get("/api/v1/payslips/my-payslips", headers=headers)
    assert payslips_res.status_code == 200
    payslips = payslips_res.json()
    assert len(payslips) >= 1
    p = payslips[0]
    assert p["gross_pay"] > 0
    assert p["net_pay"] > 0
    assert "Synthetic demonstration payslip" in p["synthetic_disclaimer"]

def test_college_industry_configuration(client):
    # Verify college instructor workflow
    res = client.post("/api/v1/auth/login", json={
        "email": "worker.college@fairshift.io",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["organization_industry"] == "education"
    assert "College" in data["user"]["organization_name"]
