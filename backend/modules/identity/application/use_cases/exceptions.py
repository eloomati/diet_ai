class IdentityApplicationError(Exception):
    pass


class UserAlreadyExistsError(IdentityApplicationError):
    pass


class InvalidCredentialsError(IdentityApplicationError):
    pass


class UserNotFoundError(IdentityApplicationError):
    pass

class InvalidRefreshTokenError(IdentityApplicationError):
    pass


class InvalidCaptchaError(IdentityApplicationError):
    pass