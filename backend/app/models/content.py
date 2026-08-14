from datetime import datetime, timezone, date

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..core.database import Base


class Content(Base):
    __tablename__ = "contents"

    id = Column(String(32), primary_key=True)
    owner_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    tags = Column(JSONB, default=[])  # DB 实际为 jsonb（原 ARRAY(String) 与 DDL 不符）
    summary = Column(Text, nullable=False)
    body = Column(Text, nullable=True)
    status = Column(String(32), default="draft", index=True)  # draft / pending_review / published / rejected
    version = Column(Integer, default=1)
    pinned = Column(Boolean, default=False)
    published_at = Column(Date, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    audit_trail = Column(JSONB, default=[])  # [{operator, operated_at, result, reason}]
    published_snapshot = Column(JSONB, nullable=True)
    weekly_query_count = Column(Integer, default=0)
    weekly_recommend_count = Column(Integer, default=0)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # DB 列名为 deleted_at（软删除时间戳），非 is_deleted
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="contents", lazy="joined")
