"""AI #3 — Care Plan Copilot. Structures what the doctor wrote. Invents nothing."""
from ai.client import call_json, load_prompt
from ai.guardrails import items_grounded_in_source

FALLBACK = {"ok": False, "items": [], "unparsed_text": "", "warnings": ["AI unavailable — enter items manually"]}


def structure_care_plan(raw_text: str, patient_ctx: dict) -> dict:
    out = call_json(load_prompt("copilot"), f"Today's date context: {patient_ctx.get('created_at','')}\n\nDoctor's plan:\n{raw_text}")
    if not out or "items" not in out:
        return {**FALLBACK, "unparsed_text": raw_text}
    invented = items_grounded_in_source(out["items"], raw_text)
    if invented:
        out["items"] = [i for i in out["items"] if i.get("title") not in invented]
        out.setdefault("warnings", []).append(f"Removed items not found in doctor's text: {invented}")
    out["ok"] = True
    out.setdefault("unparsed_text", "")
    out.setdefault("warnings", [])
    return out
