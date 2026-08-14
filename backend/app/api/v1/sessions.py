"""会话管理"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...middleware.deps import get_current_user
from ...models.session import Session, Message
from ...schemas.sessions import SessionResponse, MessageResponse, PaginatedResponse

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
