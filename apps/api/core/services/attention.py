"""
Rule-based attention engine. NO AI. NO risk scores.
Every item carries plain factual reasons. See docs/core.md for the rule table.
"""
from datetime import datetime
from core.models import AttentionItem, CareEvent, Patient, PatientQuery, Report
from core.services import audit

NO_RESPONSE_STREAK = 3
QUERY_OPEN_HOURS = 24
STREAK_TEXT = "consecutive daily check-ins unanswered"


def raise_item(db, patient: Patient, label: str, reason: str) -> AttentionItem:
    """Add reason to an existing open item of same label, or create a new one."""
    existing = (db.query(AttentionItem)
                .filter_by(patient_id=patient.id, label=label)
                .filter(AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"]))
                .first())
    if existing:
        if reason not in existing.reasons:
            existing.reasons = existing.reasons + [reason]
        return existing
    item = AttentionItem(patient_id=patient.id, patient_name=patient.name, label=label, reasons=[reason])
    db.add(item)
    return item


def concern_reason(summary: str) -> str:
    return f"New patient concern logged: {summary}"


def report_reason(title: str) -> str:
    return f"New report awaiting review: {title}"


def _is_unresolved_reason(reason: str, summary: str) -> bool:
    """'Query unresolved for {hours}h: {summary}' — hours change between runs."""
    return reason.startswith("Query unresolved for ") and reason.endswith(f": {summary}")


def query_reasons(summary: str):
    """Matcher for every reason a query can put on the QUERY item (new concern + unresolved >24h)."""
    return lambda r: r == concern_reason(summary) or _is_unresolved_reason(r, summary)


def clear_reason(db, patient: Patient, label: str, reason, actor) -> list[AttentionItem]:
    """Remove reason (exact text, or a matcher function) from the patient's open items of this label.
    An item left with no reasons is CLOSED. Every change is audited. Returns the items changed.
    Report reviewed → clear_reason(db, p, "NEEDS_REVIEW", report_reason(r.title), actor)."""
    matches = reason if callable(reason) else (lambda r: r == reason)
    items = (db.query(AttentionItem)
             .filter_by(patient_id=patient.id, label=label)
             .filter(AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"]))
             .all())
    changed = []
    for item in items:
        kept = [r for r in item.reasons if not matches(r)]
        if len(kept) == len(item.reasons):
            continue
        before = {"reasons": item.reasons, "status": item.status}
        item.reasons = kept
        if not kept:
            item.status = "CLOSED"
        audit.log(db, actor, "attention_closed" if not kept else "attention_reason_cleared",
                  "attention_item", item.id, before, {"reasons": item.reasons, "status": item.status})
        changed.append(item)
    return changed


def _raise_replacing(db, patient: Patient, label: str, reason: str, is_older_version) -> AttentionItem:
    """raise_item for reasons whose count/hours change between runs: the older wording is dropped first."""
    existing = (db.query(AttentionItem)
                .filter_by(patient_id=patient.id, label=label)
                .filter(AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"]))
                .first())
    if existing and reason not in existing.reasons:
        existing.reasons = [r for r in existing.reasons if not is_older_version(r)]
    item = raise_item(db, patient, label, reason)
    db.flush()  # session has autoflush off; the next raise_item must see this one
    return item


def _unanswered_streak(db, patient: Patient) -> list[CareEvent]:
    """Most recent run of back-to-back NO_RESPONSE events, oldest first. Still-open events are skipped."""
    events = (db.query(CareEvent)
              .filter(CareEvent.patient_id == patient.id)
              .order_by(CareEvent.scheduled_at.desc()).all())
    streak = []
    for e in events:
        if e.status in {"UPCOMING", "CURRENT"}:
            continue
        if e.status != "NO_RESPONSE":
            break
        streak.append(e)
    return streak[::-1]


def recompute_for_patient(db, patient: Patient, now: datetime | None = None):
    """Scan events/queries/reports and call raise_item per rule in docs/core.md."""
    now = now or datetime.utcnow()
    db.flush()

    streak = _unanswered_streak(db, patient)
    if len(streak) >= NO_RESPONSE_STREAK:
        dates = list(dict.fromkeys(f"{e.scheduled_at:%d %b}" for e in streak))
        _raise_replacing(db, patient, "FOLLOW_UP",
                         f"{len(streak)} {STREAK_TEXT}: {', '.join(dates)}",
                         lambda r: STREAK_TEXT in r)

    queries = (db.query(PatientQuery)
               .filter(PatientQuery.patient_id == patient.id, PatientQuery.status != "RESOLVED")
               .order_by(PatientQuery.created_at).all())
    for q in queries:
        hours = int((now - q.created_at).total_seconds() // 3600)
        if hours > QUERY_OPEN_HOURS:
            _raise_replacing(db, patient, "QUERY",
                             f"Query unresolved for {hours}h: {q.summary}",
                             lambda r, s=q.summary: _is_unresolved_reason(r, s))

    reports = (db.query(Report)
               .filter(Report.patient_id == patient.id, Report.reviewed == False)  # noqa: E712
               .order_by(Report.uploaded_at).all())
    for r in reports:
        raise_item(db, patient, "NEEDS_REVIEW", report_reason(r.title))
        db.flush()
