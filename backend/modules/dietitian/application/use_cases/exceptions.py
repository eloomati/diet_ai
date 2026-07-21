class DietitianApplicationError(Exception):
    pass


class DietitianApplicationAlreadyExistsError(DietitianApplicationError):
    pass


class DietitianApplicationNotFoundError(DietitianApplicationError):
    pass


class DietitianProfileError(Exception):
    pass


class DietitianProfileNotFoundError(DietitianProfileError):
    pass


class DietitianNotFoundError(Exception):
    pass
