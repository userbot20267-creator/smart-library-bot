"""نموذج التعليقات"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Comment(Base):
    """جدول التعليقات"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    user = relationship("User", back_populates="comments")
    book = relationship("Book", back_populates="comments")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

    @property
    def likes_count(self):
        return len(self.likes)


class CommentLike(Base):
    """جدول إعجابات التعليقات"""
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    user = relationship("User", back_populates="comment_likes")
    comment = relationship("Comment", back_populates="likes")
