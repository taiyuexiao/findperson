"""当前用户"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import verify_password, hash_password
from ...middleware.deps import get_current_user
from ...schemas.people import PersonResponse, PersonUpdateRequest
from ...schemas.auth import ChangePasswordRequest
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


@router.put("/password", summary="Change My Password", description="修改自己的密码（验旧改新）")
def change_my_password(body: ChangePasswordRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码不正确")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "密码已修改"}
