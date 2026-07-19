class DietitianDomainError(Exception):
    pass


class InvalidDietitianApplicationError(DietitianDomainError):
    pass


class InvalidDietitianProfileError(DietitianDomainError):
    pass


class ApplicationAlreadyReviewedError(DietitianDomainError):
    pass


class PhotoLimitExceededError(DietitianDomainError):
    pass
