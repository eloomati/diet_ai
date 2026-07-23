from pydantic import BaseModel

from backend.modules.identity.domain.value_objects.role import Role


class ChangeUserRoleRequest(BaseModel):
    new_role: Role


class ChangeUserRoleResponse(BaseModel):
    user_id: str
    email: str
    role: str
