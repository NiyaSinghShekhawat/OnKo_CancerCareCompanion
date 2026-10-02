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
        print("Seeded: 8 patients (one per journey state), events, 1 report, 2 queries, 6 caregivers, 4 attention items")
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
                       preferred_language="Hindi", diagnosis_label="Stage III Colorectal Adenocarcinoma (as recorded)",
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
        p.journey_chapter = 1
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
        # Fixed ids (cg_<first name>) so demo logins and tests survive a reseed, like the p_<name> patient ids.
        m.Caregiver(id="cg_sunita", patient_id="p_rajesh", name="Sunita Kumar", relation="Wife",
                    phone_whatsapp="whatsapp:+910000000010", consent_status="GRANTED",
                    permissions={"view_journey": True, "upload_reports": True, "receive_escalations": True}),
        m.Caregiver(id="cg_karthik", patient_id="p_priya", name="Karthik Sundaram", relation="Brother",
                    phone_whatsapp="whatsapp:+910000000011", consent_status="PENDING"),
    ])

    db.add_all([
        m.AttentionItem(patient_id="p_rajesh", patient_name="Rajesh Kumar", label="NEEDS_REVIEW",
                        reasons=["Medication reported missed: Capecitabine evening dose",
                                 "New report awaiting review: CBC — 20 Sep"]),
        m.AttentionItem(patient_id="p_rajesh", patient_name="Rajesh Kumar", label="QUERY",
                        reasons=["New patient concern logged: Patient reports nausea since yesterday and mild discomfort."]),
        m.AttentionItem(patient_id="p_arjun", patient_name="Arjun Reddy", label="FOLLOW_UP",
                        reasons=["3 consecutive daily check-ins unanswered"], assigned_to="nurse_anita"),
    ])
    db.flush()

    _load_other_journey_states(db, now, d)


def _load_other_journey_states(db, now, d):
    """One patient per remaining journey state. Their attention comes from the real rules (raise_item /
    raise_missed / recompute_for_patient), so the seed shows exactly what the app would produce."""
    from core.services import attention

    def patient(pid, name, age, gender, n, language, diagnosis, state, previous, changed_days_ago, chapter=1, **kw):
        return m.Patient(id=pid, name=name, age=age, gender=gender, phone_whatsapp=f"whatsapp:+9100000000{n:02d}",
                         preferred_language=language, diagnosis_label=diagnosis, doctor_id="doc_mehta",
                         journey_state=state, previous_journey_state=previous,
                         journey_state_changed_at=d(-changed_days_ago), journey_chapter=chapter, **kw)

    def caregiver(pid, name, relation, n):
        return m.Caregiver(id=f"cg_{name.split()[0].lower()}", patient_id=pid, name=name, relation=relation, phone_whatsapp=f"whatsapp:+9100000000{n:02d}",
                           consent_status="GRANTED",
                           permissions={"view_journey": True, "upload_reports": True, "receive_escalations": True})

    def done(pid, type_, title, when, chapter=None):
        return m.CareEvent(patient_id=pid, type=type_, title=title, scheduled_at=when, status="COMPLETED",
                           response_state="COMPLETED", responded_at=when, journey_chapter=chapter)

    def upcoming(pid, type_, title, when, chapter=None, **kw):
        return m.CareEvent(patient_id=pid, type=type_, title=title, scheduled_at=when, status="UPCOMING",
                           journey_chapter=chapter, **kw)

    meera = patient("p_meera", "Meera Iyer", 67, "F", 4, "Tamil", "Pancreatic Adenocarcinoma (as recorded)",
                    "PALLIATIVE", "ACTIVE_TREATMENT", 14, regimen_label="Comfort-care plan (as recorded)")
    vikram = patient("p_vikram", "Vikram Singh", 49, "M", 5, "Hindi", "Gastric Carcinoma (as recorded)",
                     "TRANSFER_OF_CARE", "ACTIVE_TREATMENT", 2, regimen_label="FLOT", cycle_current=2, cycle_total=4)
    farhan = patient("p_farhan", "Farhan Ali", 36, "M", 6, "English", "Hodgkin Lymphoma (as recorded)",
                     "RELAPSE", "REMISSION_SURVIVORSHIP", 7, chapter=2, regimen_label="ICE", cycle_current=0, cycle_total=3)
    kamala = patient("p_kamala", "Kamala Rao", 72, "F", 7, "Telugu", "Lung Adenocarcinoma (as recorded)",
                     "DECEASED", "PALLIATIVE", 10, regimen_label="", last_reviewed_at=d(-12))
    db.add_all([meera, vikram, farhan, kamala])
    db.flush()

    meera_missed = m.CareEvent(patient_id="p_meera", type="MEDICATION", title="Paracetamol 650mg",
                               details={"dose": "650 mg", "frequency": "three times daily", "timing": "after food"},
                               scheduled_at=d(-1, 20), status="REPORTED_MISSED", response_state="REPORTED_MISSED",
                               responded_at=d(-1, 22))
    meera_query = m.PatientQuery(patient_id="p_meera", channel="whatsapp", category="MEDICATION",
                                 text="Can the evening tablet be taken after dinner instead of before?",
                                 summary="Asks whether the evening tablet can be taken after dinner instead of before.",
                                 route_to="care_team_queue")
    db.add_all([
        meera_missed, meera_query,
        done("p_meera", "APPOINTMENT", "Home-care visit by Nurse Anita", d(-3, 11)),
        upcoming("p_meera", "APPOINTMENT", "Teleconsult with Dr. Mehta", d(3, 11)),

        done("p_vikram", "TREATMENT", "FLOT Cycle 2 (Day 1)", d(-12, 10)),
        upcoming("p_vikram", "MEDICATION", "Ondansetron 4mg", d(0, 21),
                 details={"dose": "4 mg", "frequency": "as directed", "timing": "before food"}),
        upcoming("p_vikram", "INVESTIGATION", "CBC", d(1, 8)),
        upcoming("p_vikram", "APPOINTMENT", "Handover call with receiving hospital", d(2, 15)),

        # Chapter 1: first treatment course and survivorship follow-up
        done("p_farhan", "TREATMENT", "ABVD Cycle 6 (Day 1)", d(-240, 10), chapter=1),
        done("p_farhan", "INVESTIGATION", "PET-CT", d(-200), chapter=1),
        done("p_farhan", "APPOINTMENT", "Survivorship follow-up with Dr. Mehta", d(-90, 11), chapter=1),
        # Chapter 2: after the switch to RELAPSE 7 days ago
        done("p_farhan", "APPOINTMENT", "Review with Dr. Mehta", d(-6, 11), chapter=2),
        upcoming("p_farhan", "INVESTIGATION", "CBC", d(2, 8), chapter=2),
        upcoming("p_farhan", "TREATMENT", "ICE Cycle 1 (Day 1)", d(4, 10), chapter=2,
                 details={"location": "Day Care Centre"}),

        done("p_kamala", "TREATMENT", "Chemotherapy Cycle 6 (Day 1)", d(-70, 10)),
        done("p_kamala", "INVESTIGATION", "CT Thorax", d(-45)),
        done("p_kamala", "APPOINTMENT", "Teleconsult with Dr. Mehta", d(-20, 11)),

        caregiver("p_meera", "Lakshmi Iyer", "Daughter", 12),
        caregiver("p_vikram", "Harpreet Singh", "Wife", 13),
        caregiver("p_farhan", "Ayesha Ali", "Sister", 14),
        caregiver("p_kamala", "Suresh Rao", "Son", 15),
    ])
    db.flush()

    # Same calls the routes make: a new MEDICATION query raises QUERY; a reported missed dose goes through
    # raise_missed (suppressed for PALLIATIVE). Then the advance-day rules, which add nothing else here.
    attention.raise_item(db, meera, "QUERY", attention.concern_reason(meera_query.summary))
    attention.raise_missed(db, meera, meera_missed)
    db.flush()
    for p in (meera, vikram, farhan, kamala):
        attention.recompute_for_patient(db, p, now)


if __name__ == "__main__":
    run()
