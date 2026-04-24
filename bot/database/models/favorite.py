"""نموذج المفضلة"""
from sqlalchemy import Column, Integer, ForeignKey, BigInteger, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base


class Favorite(Base):
    """جدول المفضلة"""
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")
