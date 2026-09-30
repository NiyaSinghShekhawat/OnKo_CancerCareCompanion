"""Demo auth: role + user id come from headers. Good enough for a prototype, clearly labeled."""
from fastapi import Header, HTTPException


class Actor:
    def __init__(self, role: str, user_id: str):
        self.role, self.user_id = role, user_id


def get_actor(x_role: str = Header("doctor"), x_user_id: str = Header("doc_mehta")) -> Actor:
    if x_role not in {"doctor", "patient", "caregiver", "care_team"}:
        raise HTTPException(400, "Unknown role")
    return Actor(x_role, x_user_id)


def require(actor: Actor, *roles: str):
    if actor.role not in roles:
        raise HTTPException(403, f"Role '{actor.role}' cannot do this")
