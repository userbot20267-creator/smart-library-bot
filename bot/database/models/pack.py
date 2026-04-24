"""نموذج الباقات"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Pack(Base, TimestampMixin):
    """جدول الباقات"""
    __tablename__ = "packs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # برمجة، تطوير ذات، إلخ
    is_active = Column(Boolean, default=True)

    # العلاقات
    items = relationship("PackItem", back_populates="pack", cascade="all, delete-orphan", order_by="PackItem.order")


class PackItem(Base):
    """جدول عناصر الباقة"""
    __tablename__ = "pack_items"

    id = Column(Integer, primary_key=True, index=True)
    pack_id = Column(Integer, ForeignKey("packs.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    order = Column(Integer, default=0)
    notes = Column(Text)  # ملاحظات عن الكتاب في هذا المسار

    # العلاقات
    pack = relationship("Pack", back_populates="items")
    book = relationship("Book", back_populates="pack_items")
