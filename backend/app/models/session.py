import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(256), default="新会话")
    summary = Column(Text, default="")
    turn_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # DB 已有列（软删除），模型补齐
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("Message", back_populates="session", lazy="dynamic",
                            order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    session_id = Column(String(32), ForeignKey("sessions.id"), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    intent = Column(String(64), nullable=True)
    domains = Column(JSONB, nullable=True)          # 领域词命中结果
    tokens = Column(JSONB, nullable=True)           # 关键词抽取结果
    confidence = Column(Integer, nullable=True)     # 意图置信度
    action_type = Column(String(32), nullable=True)
    action_json = Column(JSONB, nullable=True)      # 动作结构化结果
    matches_json = Column(JSONB, nullable=True)     # 人员匹配快照
    content_hits_json = Column(JSONB, nullable=True)  # 内容命中快照
    reply_text = Column(Text, nullable=True)
    confirm_status = Column(String(16), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="messages", lazy="joined")


class QueryLog(Base):
    """查询日志，用于管理看板活动趋势"""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(32), nullable=True)
    message_id = Column(String(32), nullable=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    intent = Column(String(64), nullable=True)
    domains = Column(JSONB, nullable=True)
    tokens = Column(JSONB, nullable=True)
    confidence = Column(Integer, nullable=True)
    has_result = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
