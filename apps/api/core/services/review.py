"""
Rule-based 'since last review' summary, used when ai.summarize returns ok: false. NO AI.
Same ReviewSummary shape as contracts/ai_outputs.json. States what was recorded, never what it means.
"""
from datetime import datetime, timedelta
from itertools import groupby

STATUS_LABELS = {"COMPLETED": "Completed", "REPORTED_MISSED": "Reported missed", "NO_RESPONSE": "No response"}
STILL_OPEN = {"UPCOMING", "CURRENT", "RESCHEDULED"}
UPCOMING_DAYS = 7


def _dates(whens: list[datetime]) -> str:
    """'27, 28, 29 Sep' — each date once, month written once per run."""
    days = sorted({w.date() for w in whens})
    return ", ".join(", ".join(f"{d:%d}" for d in run) + f" {month}"
                     for month, run in groupby(days, key=lambda d: f"{d:%b}"))


def _grouped(pairs) -> dict:
    out = {}
    for key, when in pairs:
        out.setdefault(key, []).append(when)
    return out


def is_open_today(event, now: datetime) -> bool:
    """Scheduled today and still CURRENT/UPCOMING — stays in 'upcoming' even once its time has passed."""
    return event.status in {"CURRENT", "UPCOMING"} and event.scheduled_at.date() == now.date()


def fallback_summary(events, queries, reports, since: datetime | None, now: datetime | None = None) -> dict:
    """events/queries/reports are the model rows already filtered to 'since last review'."""
    now = now or datetime.utcnow()
    events = sorted(events, key=lambda e: e.scheduled_at)
    bullets = []

    for status, label in STATUS_LABELS.items():
        by_title = _grouped((e.title, e.scheduled_at) for e in events if e.status == status)
        for title, whens in by_title.items():
            repeated = len({w.date() for w in whens}) > 1
            bullets.append(f"{label}: {title}{' — ' if repeated else ', '}{_dates(whens)}")

    for q in sorted(queries, key=lambda q: q.created_at):
        bullets.append(f"New query: {q.summary or q.text}")
    for r in sorted(reports, key=lambda r: r.uploaded_at):
        bullets.append(f"New report uploaded: {r.title}")

    horizon = now + timedelta(days=UPCOMING_DAYS)
    by_slot = _grouped(((e.title, f"{e.scheduled_at:%H:%M}"), e.scheduled_at) for e in events
                       if (e.status in STILL_OPEN and now <= e.scheduled_at < horizon) or is_open_today(e, now))
    upcoming = []
    for (title, at), whens in by_slot.items():
        repeated = len({w.date() for w in whens}) > 1
        upcoming.append(f"{title} — {_dates(whens)} at {at}" if repeated else f"{title}, {_dates(whens)} {at}")

    return {"ok": True, "since": since.isoformat() if since else None,
            "bullets": list(dict.fromkeys(bullets)), "upcoming": upcoming}
