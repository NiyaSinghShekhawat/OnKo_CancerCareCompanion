"""Single LLM entry point. Swap provider here only.

call_json() NEVER raises. It returns a parsed dict, or None if:
  - no provider / key is configured (the modules then use their rule-based fallbacks)
  - the provider errors or times out
  - the model's reply isn't valid JSON after one retry
"""
import os
import json
import re
import time
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


GEMINI_DEFAULT_MODEL = "gemini-3.8-flash"   # 2.5 models are limited to legacy users; new keys need 3.x


def _gemini_model() -> str:
    """GEMINI_MODEL wins; else AI_MODEL if it names a Gemini model; else the current stable Flash."""
    explicit = (os.getenv("GEMINI_MODEL") or "").strip()
    if explicit:
        return explicit
    ai_model = (os.getenv("AI_MODEL") or "").split("#")[0].strip()
    return ai_model if ai_model.lower().startswith("gemini") else GEMINI_DEFAULT_MODEL


def _gemini(system: str, user: str) -> str:
    """Gemini over plain REST (httpx is already in requirements — no new dependency)."""
    import httpx
    model = _gemini_model()
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": os.getenv("GEMINI_API_KEY", "")},   # never in the URL: URLs end up in error logs
        json={
            "system_instruction": {"parts": [{"text": system + _JSON_RULE}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            # Gemini 3.x is tuned for its default temperature (Google advises against lowering it), so not set here.
            "generationConfig": {"responseMimeType": "application/json"},
        },
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def _status_code(exc: Exception) -> int | None:
    """Extract an HTTP status from httpx / provider SDK exceptions without importing either SDK here."""
    response = getattr(exc, "response", None)
    code = getattr(response, "status_code", None)
    if isinstance(code, int):
        return code
    code = getattr(exc, "status_code", None)
    return code if isinstance(code, int) else None


def _redact(text: str) -> str:
    """Mask any API key that might appear in an error message before it is printed."""
    for var in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        key = os.getenv(var)
        if key and len(key) > 8:
            text = text.replace(key, f"<{var} redacted>")
    return re.sub(r"([?&]key=)[^&\s'\"]+", r"\1<redacted>", text)


def call_json(system: str, user: str) -> dict | None:
    """Return parsed JSON or None. Never raises. Retries once if the reply isn't valid JSON."""
    if not ai_available():
        return None
    max_chars = int(os.getenv("AI_MAX_INPUT_CHARS", "12000"))   # cost guard: one huge paste can't run up the bill
    if len(user) > max_chars:
        user = user[:max_chars] + "\n[truncated]"
    call = _gemini if _provider() == "gemini" else _anthropic
    for attempt in range(2):
        try:
            out = _parse(call(system, user))
            if out is not None:
                return out
            print(f"[ai.client] reply was not valid JSON (attempt {attempt + 1})")
        except Exception as e:  # noqa: BLE001
            status = _status_code(e)
            print(f"[ai.client] {_provider()} error: {_redact(str(e))}")
            if attempt == 0 and status in {429, 503}:
                delay = float(os.getenv("AI_TRANSIENT_RETRY_SECONDS", "1.5"))
                delay = min(2.0, max(1.0, delay))
                print(f"[ai.client] transient HTTP {status}; retrying once in {delay:.1f}s")
                time.sleep(delay)
                continue
            return None
    return None


def load_prompt(name: str) -> str:
    with open(os.path.join(os.path.dirname(__file__), "prompts", f"{name}.md"), encoding="utf-8") as f:
        return f.read()
