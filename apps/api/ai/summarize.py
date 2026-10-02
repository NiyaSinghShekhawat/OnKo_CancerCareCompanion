"""AI #2 — factual 'since last review' and pre-consult brief. What was recorded, not what it means.

The bullets are built DETERMINISTICALLY from the records first, so Patient 360 always has a summary even with no
AI key. If an LLM is configured it may only re-phrase / merge those bullets; its version is used only if every
bullet passes the guardrails and contains no number that isn't in the facts.
"""
import json
import re
from collections import defaultdict
from datetime import datetime
from ai.client import call_json, load_prompt, today_ist
from ai.dates import fmt_short
from ai.guardrails import has_clinical_language

EMPTY = {"ok": False, "since": None, "bullets": [], "upcoming": []}
ROUTE_WORDS = {"care_team_queue": "routed to care team", "admin_queue": "routed to admin desk", "doctor": "routed to doctor"}
MAX_UPCOMING = 5


def _dt(v) -> datetime | None:
    if isinstance(v, datetime):
        return v.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def _after(v, since: datetime | None) -> bool:
    d = _dt(v)
    return since is None or (d is not None and d >= since)


def _join_days(dates: list[str]) -> str:
    """['2026-09-21', '2026-09-22'] -> '21, 22 Sep'"""
    ds = sorted({x[:10] for x in dates if x})
    if not ds:
        return ""
    parts = [fmt_short(d) for d in ds]
    months = {p.split()[1] for p in parts}
    return ", ".join(p.split()[0] for p in parts) + f" {parts[-1].split()[1]}" if len(months) == 1 else ", ".join(parts)


def build_facts(events: list[dict], queries: list[dict], reports: list[dict],
                since: datetime | None = None, now: datetime | None = None) -> dict:
    now = now or today_ist().replace(tzinfo=None)
    bullets: list[str] = []
    by_status: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    upcoming = []

    for e in sorted(events or [], key=lambda e: str(e.get("scheduled_at", ""))):
        at, status, title = str(e.get("scheduled_at") or ""), e.get("status"), e.get("title") or "Activity"
        when = _dt(at)
        if status in {"UPCOMING", "CURRENT"} and when and when >= now.replace(hour=0, minute=0, second=0):
            upcoming.append(f"{title} — {fmt_short(at)} {when:%H:%M}".rstrip())
            continue
        if not _after(at, since):
            continue
        if status in {"COMPLETED", "REPORTED_MISSED", "NO_RESPONSE", "CONFLICTING", "RESCHEDULED"}:
            by_status[status][title].append(at)

    labels = [("COMPLETED", "Completed"), ("REPORTED_MISSED", "Reported missed"),
              ("NO_RESPONSE", "No response recorded"), ("CONFLICTING", "Conflicting responses"),
              ("RESCHEDULED", "Rescheduled")]
    for status, label in labels:
        for title, ats in by_status.get(status, {}).items():
            n = f" ({len(ats)} times)" if len(ats) > 1 else ""
            bullets.append(f"{label}: {title}{n} — {_join_days(ats)}")

    for q in queries or []:
        if not _after(q.get("created_at"), since):
            continue
        cat = (q.get("category") or "").replace("_", " ").lower()
        route = ROUTE_WORDS.get(q.get("route_to", ""), "")
        summary = (q.get("summary") or q.get("text") or "").strip().rstrip(".")
        bullets.append(f"New query ({cat}): {summary}" + (f" — {route}" if route else ""))

    for r in reports or []:
        if not _after(r.get("uploaded_at"), since):
            continue
        by = r.get("uploaded_by_role")
        bullets.append(f"New report uploaded: {r.get('title', 'Report')}" + (f" (by {by})" if by else "")
                       + ("" if r.get("reviewed") else " — not yet reviewed"))
        for v in r.get("extracted_values") or []:
            # the spec's exact format: "Hb: 9.2 — CBC, 20 Sep" (value as printed, never interpreted)
            unit = f" {v['unit']}" if v.get("unit") else ""
            bullets.append(f"{v.get('name')}: {v.get('value')}{unit} — {r.get('title', 'Report')}")

    return {"since": since.isoformat() if since else None, "bullets": bullets, "upcoming": upcoming[:MAX_UPCOMING]}


def _numbers(s: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", s))


def _llm_polish(facts: dict) -> dict | None:
    if not facts["bullets"]:
        return None
    out = call_json(load_prompt("summarize"), json.dumps(facts, ensure_ascii=False))
    if not out or not isinstance(out.get("bullets"), list):
        return None
    allowed = _numbers(json.dumps(facts, ensure_ascii=False))
    for b in out["bullets"] + list(out.get("upcoming") or []):
        if not isinstance(b, str) or has_clinical_language(b) or not _numbers(b) <= allowed:
            return None   # one bad bullet -> distrust the whole rewrite, keep the factual version
    return {"bullets": out["bullets"], "upcoming": out.get("upcoming") or facts["upcoming"]}


def since_last_review(events: list[dict], queries: list[dict], reports: list[dict], since=None) -> dict:
    """(events, queries, reports[, since]) -> ReviewSummary. Never raises.

    `since` (optional, ISO string or datetime) = patient's last_reviewed_at. Without it, everything passed in counts.
    """
    try:
        since_dt = _dt(since) if since else None
        facts = build_facts(events, queries, reports, since_dt)
        polished = _llm_polish(facts)
        if polished:
            facts.update(polished)
        facts["bullets"] = [b for b in facts["bullets"] if not has_clinical_language(b)]
        return {"ok": True, **facts}
    except Exception as e:  # noqa: BLE001
        print(f"[ai.summarize] error: {e}")
        return dict(EMPTY)


def pre_consult_brief(patient360: dict) -> dict:
    """(patient360) -> ReviewSummary, scoped to the patient's last review."""
    since = (patient360.get("patient") or {}).get("last_reviewed_at")
    return since_last_review(patient360.get("timeline", []), patient360.get("open_queries", []),
                             patient360.get("reports", []), since=since)
