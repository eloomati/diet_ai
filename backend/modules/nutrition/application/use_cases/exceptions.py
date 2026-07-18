class NutritionApplicationError(Exception):
    pass


class NutritionProfileAlreadyExistsError(NutritionApplicationError):
    pass


class NutritionProfileNotFoundError(NutritionApplicationError):
    pass


class DietPlanNotFoundError(NutritionApplicationError):
    pass


class DietPlanExportNotFoundError(NutritionApplicationError):
    pass
