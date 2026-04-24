"""نموذج الكتاب"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Book(Base, TimestampMixin):
    """جدول الكتب"""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # الملفات
    file_id = Column(String(500))  # Telegram file_id
    file_url = Column(String(1000))  # رابط خارجي
    file_type = Column(String(20), default="pdf")  # pdf, epub, etc.
    file_size = Column(BigInteger, default=0)

    # العلاقات
    author_id = Column(Integer, ForeignKey("authors.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))

    # الإحصائيات
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)

    # AI
    ai_summary = Column(Text)
    ai_description = Column(Text)
    embedding_id = Column(String(100))  # ID في vector store

    # الحالة
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # العلاقات
    author = relationship("Author", back_populates="books")
    category = relationship("Category", back_populates="books")
    downloads = relationship("Download", back_populates="book", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="book", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="book", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="book", cascade="all, delete-orphan")
    pack_items = relationship("PackItem", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book {self.title}>"

    def get_deep_link(self, bot_username: str) -> str:
        """الحصول على رابط عميق للكتاب"""
        return f"https://t.me/{bot_username}?start=book_{self.id}"
