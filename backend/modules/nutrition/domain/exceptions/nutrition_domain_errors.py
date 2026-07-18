class NutritionDomainError(Exception):
    pass


class InvalidNutritionProfileError(NutritionDomainError):
    pass


class InvalidWeeklyObligationError(NutritionDomainError):
    pass
