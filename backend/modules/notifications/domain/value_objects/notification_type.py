from enum import StrEnum


class NotificationType(StrEnum):
    TRANSACTION_PAID = "TRANSACTION_PAID"
    # Reserved for Etap 5 Stage 2/4 (human-dietitian chat) — not emitted by
    # anything yet, but the whole point of a shared Notification entity
    # (rather than a transactions-only one) is that both event kinds land
    # in the same table without a later migration.
    NEW_MESSAGE = "NEW_MESSAGE"
