from enum import StrEnum


class Role(StrEnum):
    USER = "USER"
    DIET_USER = "DIET_USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
