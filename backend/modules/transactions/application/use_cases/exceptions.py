class TransactionApplicationError(Exception):
    pass


class DietitianNotFoundError(TransactionApplicationError):
    pass


class EmailNotVerifiedError(TransactionApplicationError):
    pass


class TransactionNotFoundError(TransactionApplicationError):
    pass
