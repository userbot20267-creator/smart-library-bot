"""نموذج المؤلف"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Author(Base, TimestampMixin):
    """جدول المؤلفين"""
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    bio = Column(Text)

    # العلاقات
    books = relationship("Book", back_populates="author")

    def __repr__(self):
        return f"<Author {self.name}>"
