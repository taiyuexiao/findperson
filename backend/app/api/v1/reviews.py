"""他画像（标签）"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...middleware.deps import get_current_user
from ...models.review import PeerReview
from ...schemas.reviews import ReviewCreateRequest, ReviewResponse, PersonTagSummary
from ...schemas.sessions import PaginatedResponse

router = APIRouter(prefix="/reviews", tags=["他画像"])


def _review_to_response(r: PeerReview) -> ReviewResponse:
    return ReviewResponse(
        id=r.id,
        personId=r.person_id,
        personName=r.person_user.name if r.person_user else None,
        reviewerId=r.reviewer_id,
        reviewer=r.reviewer_user.name if r.reviewer_user else None,
        tag=r.tag_name,
        date=str(r.created_at.date()) if r.created_at else "",
    )


@router.post("", response_model=ReviewResponse, status_code=201, summary="Create Review", description="为他⼈打标签")
def create_review(body: ReviewCreateRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if body.personId == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能为自己打标签")
    existing = db.query(PeerReview).filter(
        PeerReview.person_id == body.personId,
        PeerReview.reviewer_id == user.id,
        PeerReview.tag_name == body.tag,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该标签已存在")
    review = PeerReview(
        id=uuid.uuid4().hex[:12],
        person_id=body.personId,
        reviewer_id=user.id,
        tag_name=body.tag,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _review_to_response(review)


@router.get("/sent", summary="Get Sent Reviews", description="我发出的标签")
def get_sent_reviews(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    q = db.query(PeerReview).filter(PeerReview.reviewer_id == user.id)
    total = q.count()
    items = q.order_by(PeerReview.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [_review_to_response(r).model_dump() for r in items]


@router.get("/person/{person_id}", response_model=PersonTagSummary, summary="Get Person Tags", description="某人的标签汇总")
def get_person_tags(person_id: str, db: Session = Depends(get_db)):
    reviews = db.query(PeerReview).filter(PeerReview.person_id == person_id).all()
    tags = list(set(r.tag_name for r in reviews))
    return PersonTagSummary(person_id=person_id, tags=tags, tag_count=len(tags))


@router.get("/person/{person_id}/history", summary="Get Person Review History", description="某人的标签历史（含评价人信息）")
def get_person_review_history(
    person_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(PeerReview).filter(PeerReview.person_id == person_id)
    total = q.count()
    items = q.order_by(PeerReview.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [_review_to_response(r) for r in items]
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(items=result, total=total, page=page, page_size=page_size, pages=pages)


@router.delete("/{review_id}", summary="Delete Review", description="删除标签")
def delete_review(review_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    review = db.query(PeerReview).filter(PeerReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")
    if review.reviewer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能删除自己发出的标签")
    db.delete(review)
    db.commit()
    return {"message": "已删除"}
