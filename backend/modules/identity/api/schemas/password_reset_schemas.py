from pydantic import BaseModel, EmailStr, Field


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetRequestedResponse(BaseModel):
    message: str = "If an account with that email exists, a password reset link has been sent."


class ConfirmPasswordResetRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetConfirmedResponse(BaseModel):
    message: str = "Password has been reset successfully."
