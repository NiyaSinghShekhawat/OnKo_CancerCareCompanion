"""
Rule-based attention engine. NO AI. NO risk scores.
Every item carries plain factual reasons. See docs/core.md for the rule table.
TODO(Samprada): consecutive NO_RESPONSE rule, open-query >24h rule, unreviewed report rule.
"""
from core.models import AttentionItem, Patient


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


def recompute_for_patient(db, patient: Patient):
    """TODO(Samprada): scan events/queries/reports and call raise_item per rule."""
    pass
