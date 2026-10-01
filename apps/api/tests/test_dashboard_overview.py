"""GET /dashboard/overview (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import CareEvent
from main import app

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


def today_at(h, m=0, days=0):
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return start + timedelta(days=days, hours=h, minutes=m)


def add(*events):
    """events: (type, scheduled_at, status)"""
    db = SessionLocal()
    db.add_all([CareEvent(patient_id="p_priya", type=t, title=f"{t} {s}", scheduled_at=when, status=s)
                for t, when, s in events])
    db.commit()
    db.close()


def consultations():
    return c.get("/dashboard/overview").json()["consultations_today"]


def test_seed_has_no_appointment_today():
    assert consultations() == 0   # seeded teleconsult is in 2 days


def test_counts_todays_appointments_whatever_the_time_or_status():
    add(("APPOINTMENT", today_at(0), "UPCOMING"),          # first second of today
        ("APPOINTMENT", today_at(11), "UPCOMING"),
        ("APPOINTMENT", today_at(9), "COMPLETED"),
        ("APPOINTMENT", today_at(10), "NO_RESPONSE"),
        ("APPOINTMENT", today_at(23, 59), "CURRENT"))
    assert consultations() == 5


def test_excludes_rescheduled():
    add(("APPOINTMENT", today_at(11), "UPCOMING"),
        ("APPOINTMENT", today_at(12), "RESCHEDULED"))
    assert consultations() == 1


def test_excludes_other_days():
    add(("APPOINTMENT", today_at(23, 59, days=-1), "UPCOMING"),
        ("APPOINTMENT", today_at(0, days=1), "UPCOMING"),
        ("APPOINTMENT", today_at(11, days=-3), "CURRENT"))   # old rule counted any CURRENT appointment
    assert consultations() == 0


def test_excludes_other_event_types_today():
    add(*[(t, today_at(10), "CURRENT") for t in ("MEDICATION", "INVESTIGATION", "TREATMENT", "MILESTONE")])
    assert consultations() == 0


def test_other_counts_unchanged():
    assert c.get("/dashboard/overview").json() == {
        "active_patients": 7,            # 8 seeded, Kamala is DECEASED
        "consultations_today": 0,
        "missed_activities": 5,          # Rajesh 1 reported missed + Arjun 3 no-response + Meera 1 reported missed
        "open_queries": 2,               # Rajesh, Meera
        "reports_pending_review": 1,
        "sos_open": 0,
    }
