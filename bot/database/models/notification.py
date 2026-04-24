"""نموذج الإشعارات"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Notification(Base):
    """جدول الإشعارات"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    title = Column(String(300))
    message = Column(Text, nullable=False)
    notification_type = Column(String(50))  # new_book, new_author, system
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    user = relationship("User")
