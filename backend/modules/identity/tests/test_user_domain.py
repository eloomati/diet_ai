import backend.modules.identity.domain as domain


def test_domain_public_exports_exist() -> None:
    # entities
    assert hasattr(domain, "User")
    assert hasattr(domain, "RefreshToken")

    # value objects
    assert hasattr(domain, "Email")
    assert hasattr(domain, "PasswordHash")
    assert hasattr(domain, "UserStatus")

    # exceptions (te, których faktycznie używasz)
    assert hasattr(domain, "IdentityDomainError")
    assert hasattr(domain, "InvalidEmailError")
    assert hasattr(domain, "InvalidPasswordHashError")
    assert hasattr(domain, "InactiveUserAuthenticationError")
    assert hasattr(domain, "RefreshTokenRevokedError")