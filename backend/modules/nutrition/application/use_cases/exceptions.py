class NutritionApplicationError(Exception):
    pass


class NutritionProfileAlreadyExistsError(NutritionApplicationError):
    pass


class NutritionProfileNotFoundError(NutritionApplicationError):
    pass
