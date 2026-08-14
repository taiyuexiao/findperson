import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class PeerReview(Base):
    __tablename__ = "peer_reviews"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    person_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    reviewer_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    reviewer_name = Column(String(64), nullable=True)  # DB 已有列，模型补齐
    tag_name = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    person_user = relationship("User", back_populates="received_reviews", lazy="joined",
                               foreign_keys=[person_id])
    reviewer_user = relationship("User", back_populates="sent_reviews", lazy="joined",
                                 foreign_keys=[reviewer_id])
