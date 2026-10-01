"""Clinician-governed journey states. OnKo never infers these."""

MESSAGING_ALLOWED = {
    "ACTIVE_TREATMENT": True,
    "REMISSION_SURVIVORSHIP": True,   # survivorship cadence
    "RELAPSE": True,                  # new chapter, history kept
    "TRANSFER_OF_CARE": False,        # paused until new workflow
    "PALLIATIVE": True,               # comfort-care tone, no adherence nudges
    "DECEASED": False,                # HARD STOP
}


def can_message(state: str) -> bool:
    return MESSAGING_ALLOWED.get(state, False)


def adherence_nudges_allowed(state: str) -> bool:
    return state in {"ACTIVE_TREATMENT", "RELAPSE"}


# ---- What core does per state (attention queue, daily checklist, 24h window) ----
NO_ATTENTION = {"DECEASED"}                              # no new attention items of any kind
CHECKLIST_PAUSED = {"TRANSFER_OF_CARE", "DECEASED"}      # empty checklist, window never closes -> no NO_RESPONSE
ADHERENCE_ALERTS_OFF = {"PALLIATIVE"}                    # no missed-dose / unanswered-check-in items


def attention_allowed(state: str) -> bool:
    return state not in NO_ATTENTION


def checklist_paused(state: str) -> bool:
    return state in CHECKLIST_PAUSED


def adherence_alerts_allowed(state: str) -> bool:
    """Missed medication/treatment reported by the patient → NEEDS_REVIEW."""
    return attention_allowed(state) and state not in ADHERENCE_ALERTS_OFF


def check_in_follow_up_allowed(state: str) -> bool:
    """Consecutive NO_RESPONSE check-ins → FOLLOW_UP. Off while adherence alerts are off or the checklist is paused."""
    return adherence_alerts_allowed(state) and not checklist_paused(state)
