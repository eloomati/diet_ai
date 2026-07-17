from backend.modules.identity.infrastructure.security import BcryptPasswordHasher


def test_bcrypt_hash_and_verify() -> None:
    hasher = BcryptPasswordHasher()

    hashed = hasher.hash("StrongPass123")

    assert hashed != "StrongPass123"
    assert hasher.verify("StrongPass123", hashed) is True
    assert hasher.verify("WrongPass123", hashed) is False