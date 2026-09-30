"""AI #2 — factual 'since last review' and pre-consult brief. What was recorded, not what it means."""
import json
from ai.client import call_json, load_prompt
from ai.guardrails import has_clinical_language

EMPTY = {"ok": False, "since": None, "bullets": [], "upcoming": []}


def since_last_review(events: list[dict], queries: list[dict], reports: list[dict]) -> dict:
    payload = json.dumps({"events": events, "queries": queries, "reports": reports}, default=str)
    out = call_json(load_prompt("summarize"), payload)
    if not out or "bullets" not in out:
        return EMPTY
    out["bullets"] = [b for b in out["bullets"] if not has_clinical_language(b)]
    out["ok"] = True
    return out


def pre_consult_brief(patient360: dict) -> dict:
    return since_last_review(patient360.get("timeline", []), patient360.get("open_queries", []),
                             patient360.get("reports", []))
