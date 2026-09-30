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
