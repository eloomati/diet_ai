from backend.modules.identity.application.ports.password_hasher import PasswordHasher
from backend.shared.security import hash_password, verify_password


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, plain_password: str) -> str:
        return hash_password(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return verify_password(plain_password, password_hash)
