"""Demo data. Run: python -m core.seed   (wipes and reloads the DB)
The running app resets through POST /demo/reset, which calls run(db) with its own session."""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

from core.db import Base, engine, SessionLocal
from core import models as m


def run(db=None):
    """No session: drop + recreate tables and commit (CLI, tests).
    With a session: delete every row and reseed inside it, keeping the tables; the caller commits."""
    if db is None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            _load(db)
            db.commit()
        finally:
            db.close()
        print("Seeded: 4 patients, events, 1 report, 1 query, 2 caregivers, 3 attention items")
        return
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.expunge_all()
    _load(db)
    db.flush()


def _load(db):
    # Dates are relative to the moment of seeding, so a reset hours later still looks like "today".
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    d = lambda days, h=9: (now + timedelta(days=days)).replace(hour=h)

    db.add_all([
        m.User(id="doc_mehta", name="Dr. Mehta", role="doctor"),
        m.User(id="nurse_anita", name="Nurse Anita", role="care_team"),
    ])

    rajesh = m.Patient(id="p_rajesh", name="Rajesh Kumar", age=54, gender="M", abha_id="91-1234-5678-9012",
                       phone_whatsapp=os.getenv("DEMO_PATIENT_WHATSAPP", "whatsapp:+910000000000"),
                       preferred_language="Hindi", diagnosis_label="Stage III Colorectal Adenocarcinoma",
                       regimen_label="CAPOX", cycle_current=4, cycle_total=8, doctor_id="doc_mehta",
                       last_reviewed_at=d(-6))
    priya = m.Patient(id="p_priya", name="Priya Sundaram", age=41, gender="F", phone_whatsapp="whatsapp:+910000000001",
                      preferred_language="Tamil", diagnosis_label="Breast Carcinoma (as recorded)",
                      regimen_label="AC-T", cycle_current=2, cycle_total=8, doctor_id="doc_mehta")
    arjun = m.Patient(id="p_arjun", name="Arjun Reddy", age=63, gender="M", phone_whatsapp="whatsapp:+910000000002",
                      preferred_language="Telugu", diagnosis_label="Head & Neck SCC (as recorded)",
                      regimen_label="Concurrent chemoradiation", cycle_current=5, cycle_total=6, doctor_id="doc_mehta")
    lakshmi = m.Patient(id="p_lakshmi", name="Lakshmi Devi", age=58, gender="F", phone_whatsapp="whatsapp:+910000000003",
                        preferred_language="Telugu", diagnosis_label="Ovarian Carcinoma (as recorded)",
                        journey_state="REMISSION_SURVIVORSHIP", doctor_id="doc_mehta")
    for p in (rajesh, priya, arjun, lakshmi):
        # Current state set well before any seeded event, so advance-day still marks seeded events normally.
        p.journey_state_changed_at = d(-30)
    db.add_all([rajesh, priya, arjun, lakshmi])
    db.flush()

    db.add_all([
        m.CareEvent(patient_id="p_rajesh", type="TREATMENT", title="Chemotherapy Cycle 4 (Day 1)",
                    details={"location": "Day Care Centre", "instructions": "Pre-medication: Dexamethasone & Ondansetron"},
                    scheduled_at=d(0, 9), status="CURRENT"),
        m.CareEvent(patient_id="p_rajesh", type="MEDICATION", title="Capecitabine 500mg",
                    details={"dose": "500 mg", "frequency": "twice daily", "timing": "after food"},
                    scheduled_at=d(-1, 21), status="REPORTED_MISSED", response_state="REPORTED_MISSED"),
        m.CareEvent(patient_id="p_rajesh", type="MEDICATION", title="Capecitabine 500mg",
                    details={"dose": "500 mg", "frequency": "twice daily", "timing": "after food"},
                    scheduled_at=d(0, 21), status="UPCOMING"),
        m.CareEvent(patient_id="p_rajesh", type="INVESTIGATION", title="CBC", scheduled_at=d(-4), status="COMPLETED",
                    response_state="COMPLETED"),
        m.CareEvent(patient_id="p_rajesh", type="APPOINTMENT", title="Teleconsult with Dr. Mehta", scheduled_at=d(2, 11)),
        m.CareEvent(patient_id="p_rajesh", type="MILESTONE", title="Daily 15-min walk", scheduled_at=d(0, 18)),
        m.CareEvent(patient_id="p_priya", type="TREATMENT", title="Chemotherapy Cycle 3 (Day 1)", scheduled_at=d(1, 10)),
        *[m.CareEvent(patient_id="p_arjun", type="MEDICATION", title="Daily check-in", scheduled_at=d(-i),
                      status="NO_RESPONSE", response_state="NO_RESPONSE") for i in (1, 2, 3)],
    ])

    db.add(m.Report(patient_id="p_rajesh", title="CBC — 20 Sep", uploaded_by_role="caregiver",
                    text="Haemoglobin 9.2 g/dL (12-15)\nWBC 4.1 x10^9/L (4-11)\nPlatelets 180 x10^9/L (150-400)",
                    extracted_values=[{"name": "Hb", "value": "9.2", "unit": "g/dL",
                                       "reference_range_as_printed": "12-15",
                                       "source_line": "Haemoglobin 9.2 g/dL (12-15)"}]))
    db.add(m.PatientQuery(patient_id="p_rajesh", text="Feeling nauseous since yesterday, mild discomfort",
                          channel="whatsapp", category="SYMPTOM_CONCERN",
                          summary="Patient reports nausea since yesterday and mild discomfort.",
                          route_to="care_team_queue"))
    db.add_all([
        m.Caregiver(patient_id="p_rajesh", name="Sunita Kumar", relation="Wife",
                    phone_whatsapp="whatsapp:+910000000010", consent_status="GRANTED",
                    permissions={"view_journey": True, "upload_reports": True, "receive_escalations": True}),
        m.Caregiver(patient_id="p_priya", name="Karthik Sundaram", relation="Brother",
                    phone_whatsapp="whatsapp:+910000000011", consent_status="PENDING"),
    ])

    db.add_all([
        m.AttentionItem(patient_id="p_rajesh", patient_name="Rajesh Kumar", label="NEEDS_REVIEW",
                        reasons=["Medication reported missed: Capecitabine evening dose",
                                 "New report awaiting review: CBC — 20 Sep"]),
        m.AttentionItem(patient_id="p_rajesh", patient_name="Rajesh Kumar", label="QUERY",
                        reasons=["New patient concern logged: Patient reports nausea since yesterday and mild discomfort."]),
        m.AttentionItem(patient_id="p_arjun", patient_name="Arjun Reddy", label="FOLLOW_UP",
                        reasons=["3 consecutive daily check-ins unanswered"]),
    ])


if __name__ == "__main__":
    run()
