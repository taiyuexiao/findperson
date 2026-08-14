from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DepartmentBrief(BaseModel):
    """部门简要信息"""
    id: int
    name: str

    model_config = {"from_attributes": True}


class PersonResponse(BaseModel):
    """人员详情响应"""
    id: str
    account: str
    name: str
    phone: str | None = None
    system_role: str
    department_id: int | None = None
    # 前端以字符串消费部门(与 auth/me 返回一致);ORM Department 对象在 validator 中转 name
    department: str | None = None
    role: str | None = None
    contact: str | None = None
    domains: list | None = None
    self_portrait: str | None = None
    completeness: int
    recommended_count: int
    active: bool
    last_login_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("department", mode="before")
    @classmethod
    def _dept_to_name(cls, v):
        if v is None or isinstance(v, str):
            return v
        return getattr(v, "name", None)


class PersonUpdateRequest(BaseModel):
    """更新人员信息（可选字段全部可空，支持 camelCase 别名以兼容前端）"""
    phone: str | None = Field(None, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=64)
    departmentId: int | None = None
    role: str | None = Field(None, max_length=128)
    contact: str | None = Field(None, max_length=64)
    domains: list[str] | None = None
    selfPortrait: str | None = None
    systemRole: str | None = None
    active: bool | None = None

    model_config = {"populate_by_name": True}
