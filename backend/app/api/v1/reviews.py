"""他画像（标签）"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...middleware.deps import get_current_user
from ...models.review import PeerReview
from ...schemas.reviews import ReviewCreateRequest, ReviewResponse, PersonTagSummary
from ...schemas.sessions import PaginatedResponse
from ...services.publish_event import emit_publish_event, PERSON_CHANGED
from ...services.tag_sync import sync_tag_to_agent

router = APIRouter(prefix="/reviews", tags=["他画像"])


def _sync_review_to_agent_tags(db: Session, *, person_id: str, tag: str, active: bool) -> None:
    """画像评价同步进 Agent 标签体系(代理到 services.tag_sync 公共实现)。"""
    sync_tag_to_agent(db, person_id=person_id, tag=tag, active=active,
                      source="peer_review", created_by="review-api")


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
        # v4 §五:相同评价人/对象/事项的重复提交按更新处理,不产生重复记录
        existing.created_at = datetime.now(timezone.utc)
        _sync_review_to_agent_tags(db, person_id=body.personId, tag=body.tag, active=True)
        emit_publish_event(db, PERSON_CHANGED, body.personId, created_by=user.id)
        db.commit()
        db.refresh(existing)
        return _review_to_response(existing)
    review = PeerReview(
        id=uuid.uuid4().hex[:12],
        person_id=body.personId,
        reviewer_id=user.id,
        tag_name=body.tag,
    )
    db.add(review)
    _sync_review_to_agent_tags(db, person_id=body.personId, tag=body.tag, active=True)
    # 发事件:agent-service 消费后重建该人员的 OKF/RAG 索引(画像进知识检索)
    emit_publish_event(db, PERSON_CHANGED, body.personId, created_by=user.id)
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
    _sync_review_to_agent_tags(db, person_id=review.person_id, tag=review.tag_name, active=False)
    emit_publish_event(db, PERSON_CHANGED, review.person_id, created_by=user.id)
    db.commit()
    return {"message": "已删除"}
