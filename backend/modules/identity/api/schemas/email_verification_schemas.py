from pydantic import BaseModel


class ConfirmEmailVerificationRequest(BaseModel):
    token: str


class EmailVerificationConfirmedResponse(BaseModel):
    message: str = "Email verified successfully."
