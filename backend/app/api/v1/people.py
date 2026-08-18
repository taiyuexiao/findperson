"""人员管理"""
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import hash_password
from ...middleware.deps import require_admin
from ...models.user import User
from ...schemas.people import PersonCreateRequest, PersonResponse, PersonUpdateRequest
from ...services.publish_event import emit_publish_event, PERSON_CHANGED

router = APIRouter(prefix="/people", tags=["人员"])


@router.get("", summary="List People", description="人员列表（分页 + 搜索）")
def list_people(
    keyword: str | None = Query(None, description="姓名或账号搜索"),
    department_id: int | None = None,
    domain: str | None = None,
    active: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),  # 名片库/详情一次性拉全量(当前数据量级 252)
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if active:
        q = q.filter(User.active == True)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter((User.name.ilike(kw)) | (User.account.ilike(kw)))
    if department_id:
        q = q.filter(User.department_id == department_id)
    total = q.count()
    items = q.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()
    # 直接返回数组（前端需要平铺列表）
    return [PersonResponse.model_validate(u).model_dump() for u in items]


@router.post("", response_model=PersonResponse, status_code=201, summary="Create Person", description="新增成员(仅管理员)")
def create_person(body: PersonCreateRequest, request: Request, db: Session = Depends(get_db)):
    require_admin(request)  # v4 §十:成员管理仅管理员
    if body.account and db.query(User).filter(User.account == body.account).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号已存在")
    # 生成 id/账号:沿用 p-XXXX / PXXXX 序列
    max_num = 0
    for (uid,) in db.query(User.id).all():
        m = re.fullmatch(r"p-(\d+)", uid or "")
        if m:
            max_num = max(max_num, int(m.group(1)))
    new_id = f"p-{max_num + 1:04d}"
    # 登录账号约定为手机号(contact 优先,其次 phone),密码统一默认 123456
    account = body.account or (body.contact or "").strip() or (body.phone or "").strip() or f"P{max_num + 1:04d}"
    # 默认上级 = 部门负责人
    manager_id = body.managerId
    if not manager_id and body.departmentId:
        from ...models.department import Department
        dept = db.query(Department).filter(Department.id == body.departmentId).first()
        manager_id = dept.leader_id if dept else None
    user = User(
        id=new_id,
        account=account,
        name=body.name,
        password_hash=hash_password(body.password or "123456"),
        phone=body.phone,
        system_role=body.systemRole or "普通成员",
        department_id=body.departmentId,
        role=body.role,
        contact=body.contact,
        active=body.active if body.active is not None else True,
        manager_id=manager_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    emit_publish_event(db, PERSON_CHANGED, user.id, created_by=getattr(request.state, "user_id", None))
    db.commit()
    return user


@router.get("/{person_id}", response_model=PersonResponse, summary="Get Person", description="人员详情")
def get_person(person_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == person_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="人员不存在")
    return user


@router.patch("/{person_id}", response_model=PersonResponse, summary="Update Person", description="更新人员信息(仅管理员)")
def update_person(person_id: str, body: PersonUpdateRequest, request: Request, db: Session = Depends(get_db)):
    require_admin(request)  # v4 §十:成员管理仅管理员(本人改资料走 /me/profile)
    user = db.query(User).filter(User.id == person_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="人员不存在")
    update_data = body.model_dump(exclude_unset=True)
    field_map = {
        "departmentId": "department_id",
        "selfPortrait": "self_portrait",
        "systemRole": "system_role",
        "managerId": "manager_id",
    }
    for camel, snake in field_map.items():
        if camel in update_data:
            update_data[snake] = update_data.pop(camel)

    # 部门变更且未显式指定上级时,默认上级 = 新部门负责人
    if "department_id" in update_data and "manager_id" not in update_data:
        from ...models.department import Department
        new_dept = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        update_data["manager_id"] = new_dept.leader_id if new_dept else None

    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    emit_publish_event(db, PERSON_CHANGED, user.id, created_by=getattr(request.state, "user_id", None))
    db.commit()
    return user


@router.get("/{person_id}/reviews", summary="Get Person Reviews", description="某人的标签历史")
def get_person_reviews(
    person_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from ...models.review import PeerReview
    from ...schemas.reviews import ReviewResponse
    from ...schemas.sessions import PaginatedResponse

    q = db.query(PeerReview).filter(PeerReview.person_id == person_id)
    total = q.count()
    items = q.order_by(PeerReview.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for r in items:
        result.append(ReviewResponse(
            id=r.id,
            personId=r.person_id,
            personName=r.person_user.name if r.person_user else None,
            reviewerId=r.reviewer_id,
            reviewer=r.reviewer_user.name if r.reviewer_user else None,
            tag=r.tag_name,
            date=str(r.created_at.date()) if r.created_at else "",
        ))
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(items=result, total=total, page=page, page_size=page_size, pages=pages)
