"""当前用户"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...middleware.deps import get_current_user
from ...schemas.people import PersonResponse, PersonUpdateRequest
from ...models.user import User

router = APIRouter(prefix="/me", tags=["当前用户"])


@router.get("", response_model=PersonResponse, summary="Get Me", description="当前登录用户信息")
def get_me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return user


@router.put("/profile", response_model=PersonResponse, summary="Update My Profile", description="更新当前用户自己的资料")
def update_my_profile(body: PersonUpdateRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    update_data = body.model_dump(exclude_unset=True)
    # 映射 camelCase → snake_case
    field_map = {
        "departmentId": "department_id",
        "selfPortrait": "self_portrait",
        "systemRole": "system_role",
    }
    for camel, snake in field_map.items():
        if camel in update_data:
            update_data[snake] = update_data.pop(camel)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
