class AdminApplicationError(Exception):
    pass


class CannotDeleteSelfError(AdminApplicationError):
    pass
