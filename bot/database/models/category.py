"""نموذج الأقسام"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """جدول الأقسام"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # العلاقات
    books = relationship("Book", back_populates="category")
    subcategories = relationship("Category", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<Category {self.name}>"
