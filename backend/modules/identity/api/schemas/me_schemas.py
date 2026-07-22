from pydantic import BaseModel, EmailStr


class MeResponse(BaseModel):
    user_id: str
    email: EmailStr
    status: str
    role: str
    email_verified: bool
    display_name: str | None = None


class UpdateMeRequest(BaseModel):
    # Explicit None clears it — a user can always go back to their email
    # as their shown identity, not just set one once and be stuck with it.
    display_name: str | None = None
