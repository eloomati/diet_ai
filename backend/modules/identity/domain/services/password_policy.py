import re

from backend.modules.identity.domain.exceptions.identity_domain_errors import InvalidPasswordError


class PasswordPolicy:
    @staticmethod
    def validate(password: str) -> None:
        if len(password) < 8:
            raise InvalidPasswordError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", password):
            raise InvalidPasswordError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise InvalidPasswordError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", password):
            raise InvalidPasswordError("Password must contain at least one digit.")