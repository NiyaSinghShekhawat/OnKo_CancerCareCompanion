import os


def send(to: str, body: str) -> bool:
    sid, token = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    if not sid or not token or not from_number:
        print(f"[whatsapp:dry-run] -> {to}\n{body}\n")
        return False
    from twilio.rest import Client
    Client(sid, token).messages.create(from_=from_number, to=to, body=body)
    return True


def render_enrollment_otp(otp: str) -> str:
    return (
        "OnKo number verification\n\n"
        f"Your verification code is: {otp}\n"
        "This code expires in 10 minutes. Share it only with the care-team member enrolling you."
    )


def render_patient_access(patient_name: str, patient_id: str, password: str, login_url: str) -> str:
    first = patient_name.split()[0] if patient_name.split() else "there"
    return (
        f"Welcome to OnKo, {first}. Your care team has created your patient dashboard.\n\n"
        f"Patient ID: {patient_id}\n"
        f"Password: {password}\n"
        f"Login: {login_url}\n\n"
        "Keep this password private. You can reuse it to sign in until it is changed. OnKo organizes your recorded care journey; clinical decisions remain with your care team."
    )


def render_checklist(patient_name: str, items: list[dict]) -> str:
    lines = [f"Namaste {patient_name.split()[0]}, here is today's care checklist from your care team:\n"]
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it['title']} — {it['scheduled_at'][11:16]}")
    lines.append("\nReply like: 1 done, 2 missed")
    lines.append("You have 24 hours to update. Reply HI for menu, SOS for urgent help.")
    return "\n".join(lines)


MENU = ("OnKo menu:\n1️⃣ Medication\n2️⃣ Query / Need help\n🆘 Reply SOS for urgent help\n\n"
        "For urgent help, your caregiver and care team will be alerted.")


def render_caregiver_access(caregiver_name: str, patient_name: str, caregiver_id: str, password: str, login_url: str) -> str:
    first = caregiver_name.split()[0] if caregiver_name.split() else "there"
    patient_first = patient_name.split()[0] if patient_name.split() else patient_name
    return (
        f"Welcome to OnKo, {first}. {patient_first} has granted you caregiver dashboard access.\n\n"
        f"Caregiver ID: {caregiver_id}\n"
        f"Password: {password}\n"
        f"Login: {login_url}\n\n"
        "Keep this password private. Access remains controlled by the patient and may be changed or revoked by them."
    )
