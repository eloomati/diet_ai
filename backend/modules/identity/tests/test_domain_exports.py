from backend.modules.identity import domain


def test_domain_public_exports_exist() -> None:
    assert domain.User is not None
    assert domain.RefreshToken is not None
    assert domain.Email is not None
    assert domain.PasswordHash is not None
    assert domain.UserStatus is not None
    assert domain.UserRegistered is not None
    assert domain.UserLoggedIn is not None
    assert domain.UserRepository is not None
    assert domain.PasswordPolicy is not None
    assert domain.IdentityDomainError is not None
    assert domain.InvalidEmailError is not None
    assert domain.InvalidPasswordError is not None
    assert domain.InvalidPasswordHashError is not None
    assert domain.InactiveUserAuthenticationError is not None
    assert domain.RefreshTokenRevokedError is not None