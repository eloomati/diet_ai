class IdentityDomainError(Exception):
    pass


class InvalidEmailError(IdentityDomainError):
    pass


class InvalidDisplayNameError(IdentityDomainError):
    pass


class InvalidPasswordError(IdentityDomainError):
    pass


class InvalidPasswordHashError(IdentityDomainError):
    pass


class InactiveUserAuthenticationError(IdentityDomainError):
    pass


class RefreshTokenRevokedError(IdentityDomainError):
    pass


class InvalidPasswordResetTokenError(IdentityDomainError):
    pass


class InvalidEmailVerificationTokenError(IdentityDomainError):
    pass