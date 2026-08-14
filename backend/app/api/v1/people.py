"""人员管理"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.user import User
from ...schemas.people import PersonResponse, PersonUpdateRequest

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


@router.get("/{person_id}", response_model=PersonResponse, summary="Get Person", description="人员详情")
def get_person(person_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == person_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="人员不存在")
    return user


@router.patch("/{person_id}", response_model=PersonResponse, summary="Update Person", description="更新人员信息")
def update_person(person_id: str, body: PersonUpdateRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == person_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="人员不存在")
    update_data = body.model_dump(exclude_unset=True)
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
