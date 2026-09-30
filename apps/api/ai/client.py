"""Single LLM entry point. Swap provider here only."""
import os, json, re


def call_json(system: str, user: str) -> dict | None:
    """Return parsed JSON or None. Never raises."""
    try:
        if os.getenv("AI_PROVIDER", "anthropic") == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=os.getenv("AI_MODEL", "claude-sonnet-4-6"), max_tokens=1500,
                system=system + "\nRespond with ONLY valid JSON. No markdown, no prose.",
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            text = re.sub(r"```json|```", "", text).strip()
            return json.loads(text)
        # TODO(Shreyan): Gemini branch if you prefer it
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[ai.client] error: {e}")
        return None


def load_prompt(name: str) -> str:
    with open(os.path.join(os.path.dirname(__file__), "prompts", f"{name}.md"), encoding="utf-8") as f:
        return f.read()
