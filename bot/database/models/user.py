"""نموذج المستخدم"""
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text, Float
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """جدول المستخدمين"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language_code = Column(String(10), default="ar")

    # الإحصائيات
    total_downloads = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    referral_code = Column(String(20), unique=True)
    referred_by = Column(BigInteger, nullable=True)

    # الحالة
    is_banned = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_owner = Column(Boolean, default=False)

    # الإشعارات
    notify_new_books = Column(Boolean, default=True)
    notify_new_authors = Column(Boolean, default=False)
    preferred_categories = Column(Text, default="")  # JSON string
    preferred_authors = Column(Text, default="")  # JSON string

    # العلاقات
    downloads = relationship("Download", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    comment_likes = relationship("CommentLike", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.telegram_id} - {self.first_name}>"
