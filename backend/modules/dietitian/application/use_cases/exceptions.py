class DietitianApplicationError(Exception):
    pass


class DietitianApplicationAlreadyExistsError(DietitianApplicationError):
    pass


class DietitianApplicationNotFoundError(DietitianApplicationError):
    pass
