from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    level = Column(Integer, nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    leader_id = Column(String(32), ForeignKey("users.id"), nullable=True)
    path = Column(JSONB, default=[])  # 部门路径（祖先 id 数组），DB 已有 jsonb 列，模型补齐
    responsibility = Column(Text, nullable=True)
    status = Column(String(16), default="active")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    members = relationship("User", back_populates="department", lazy="dynamic",
                           foreign_keys="User.department_id")
    children = relationship("Department", backref="parent", remote_side=[id], lazy="joined")
