"""نموذج التقييمات"""
from sqlalchemy import Column, Integer, ForeignKey, BigInteger, Float, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base


class Rating(Base):
    """جدول التقييمات"""
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    rating = Column(Float, nullable=False)  # 1-5
    rated_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    user = relationship("User", back_populates="ratings")
    book = relationship("Book", back_populates="ratings")
