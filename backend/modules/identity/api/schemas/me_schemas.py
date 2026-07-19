from pydantic import BaseModel, EmailStr


class MeResponse(BaseModel):
    user_id: str
    email: EmailStr
    status: str
    role: str
    email_verified: bool