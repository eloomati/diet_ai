import bcrypt

from backend.modules.identity.application.ports.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, plain_password: str) -> str:
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )