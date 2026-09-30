"""Single LLM entry point. Swap provider here only.

call_json() NEVER raises. It returns a parsed dict, or None if:
  - no provider / key is configured (the modules then use their rule-based fallbacks)
  - the provider errors or times out
  - the model's reply isn't valid JSON after one retry
"""
import os
import json
import re
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
_TIMEOUT = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))
_JSON_RULE = "\nRespond with ONLY one valid JSON object. No markdown fences, no prose before or after."


def today_ist() -> datetime:
    """'Today' for date resolution ("15 Oct" -> 2026-10-15). Fixed IST offset: no tzdata needed on Windows."""
    return datetime.now(IST)


def ai_available() -> bool:
    p = _provider()
    return (p == "anthropic" and bool(os.getenv("ANTHROPIC_API_KEY"))) or \
           (p == "gemini" and bool(os.getenv("GEMINI_API_KEY")))


def _provider() -> str:
    return (os.getenv("AI_PROVIDER") or "anthropic").split("#")[0].strip().lower()


def _parse(text: str) -> dict | None:
    text = re.sub(r"```(?:json)?", "", text or "").strip()
    try:
        out = json.loads(text)
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        # model wrapped the JSON in prose: take the outermost {...}
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                out = json.loads(text[start:end + 1])
                return out if isinstance(out, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def _anthropic(system: str, user: str) -> str:
    import anthropic
    client = anthropic.Anthropic(timeout=_TIMEOUT, max_retries=1)
    msg = client.messages.create(
        model=os.getenv("AI_MODEL", "claude-sonnet-4-6"), max_tokens=2000, temperature=0,
        system=system + _JSON_RULE,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _gemini(system: str, user: str) -> str:
    """Gemini over plain REST (httpx is already in requirements — no new dependency)."""
    import httpx
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": os.getenv("GEMINI_API_KEY")},
        json={
            "system_instruction": {"parts": [{"text": system + _JSON_RULE}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        },
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def call_json(system: str, user: str) -> dict | None:
    """Return parsed JSON or None. Never raises. Retries once if the reply isn't valid JSON."""
    if not ai_available():
        return None
    call = _gemini if _provider() == "gemini" else _anthropic
    for attempt in range(2):
        try:
            out = _parse(call(system, user))
            if out is not None:
                return out
            print(f"[ai.client] reply was not valid JSON (attempt {attempt + 1})")
        except Exception as e:  # noqa: BLE001
            print(f"[ai.client] {_provider()} error: {e}")
            return None
    return None


def load_prompt(name: str) -> str:
    with open(os.path.join(os.path.dirname(__file__), "prompts", f"{name}.md"), encoding="utf-8") as f:
        return f.read()
