import os


def send(to: str, body: str) -> bool:
    sid, token = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        print(f"[whatsapp:dry-run] -> {to}\n{body}\n")
        return False
    from twilio.rest import Client
    Client(sid, token).messages.create(from_=os.getenv("TWILIO_WHATSAPP_FROM"), to=to, body=body)
    return True


def render_checklist(patient_name: str, items: list[dict]) -> str:
    lines = [f"Namaste {patient_name.split()[0]}, here is today's care checklist from your care team:\n"]
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it['title']} — {it['scheduled_at'][11:16]}")
    lines.append("\nReply like: 1 done, 2 missed")
    lines.append("You have 24 hours to update. Reply HI for menu, SOS for urgent help.")
    return "\n".join(lines)


MENU = ("OnKo menu:\n1️⃣ Medication\n2️⃣ Query / Need help\n🆘 Reply SOS for urgent help\n\n"
        "For urgent help, your caregiver and care team will be alerted.")
