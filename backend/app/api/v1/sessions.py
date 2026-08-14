"""会话管理"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...middleware.deps import get_current_user
from ...models.session import Session, Message
from ...schemas.sessions import (
    MessageResponse,
    PaginatedResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionUpdateRequest,
)

router = APIRouter(prefix="/sessions", tags=["会话"])


@router.get("", summary="List Sessions", description="我的会话列表")
def list_sessions(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    q = db.query(Session).filter(Session.user_id == user.id, Session.is_active == True)
    total = q.count()
    items = q.order_by(Session.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [SessionResponse.model_validate(s) for s in items]
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(items=result, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{session_id}/messages", summary="List Messages", description="某会话的消息列表")
def list_messages(
    session_id: str,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    q = db.query(Message).filter(Message.session_id == session_id)
    total = q.count()
    items = q.order_by(Message.created_at).offset((page - 1) * page_size).limit(page_size).all()
    result = [MessageResponse.model_validate(m) for m in items]
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(items=result, total=total, page=page, page_size=page_size, pages=pages)


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Create Session", description="新建会话（前端自带 ID，幂等）")
def create_session(body: SessionCreateRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    session_id = body.id or uuid.uuid4().hex[:12]
    existing = db.query(Session).filter(Session.id == session_id).first()
    if existing:
        return existing
    session = Session(
        id=session_id,
        user_id=user.id,
        title=body.title or "新对话",
        summary=body.summary or "",
        turn_count=body.turnCount or 0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}", response_model=SessionResponse, summary="Update Session", description="更新会话（重命名 / 摘要 / 轮次）")
def update_session(session_id: str, body: SessionUpdateRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    session = db.query(Session).filter(
        Session.id == session_id, Session.user_id == user.id, Session.is_active == True
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    data = body.model_dump(exclude_unset=True)
    if data.get("title") is not None:
        session.title = data["title"]
    if data.get("summary") is not None:
        session.summary = data["summary"]
    if data.get("turnCount") is not None:
        session.turn_count = data["turnCount"]

    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", summary="Delete Session", description="软删除会话")
def delete_session(session_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    session = db.query(Session).filter(
        Session.id == session_id, Session.user_id == user.id, Session.is_active == True
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    session.is_active = False
    session.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "已删除"}
