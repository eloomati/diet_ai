class TransactionApplicationError(Exception):
    pass


class DietitianNotFoundError(TransactionApplicationError):
    pass
