"""نموذج التحميلات"""
from sqlalchemy import Column, Integer, ForeignKey, BigInteger, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base


class Download(Base):
    """جدول التحميلات"""
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    user = relationship("User", back_populates="downloads")
    book = relationship("Book", back_populates="downloads")
