class TransactionDomainError(Exception):
    pass


class InvalidTransactionError(TransactionDomainError):
    pass
