"""نموذج القنوات الإجبارية"""
from sqlalchemy import Column, Integer, String, Boolean
from .base import Base


class RequiredChannel(Base):
    """جدول القنوات الإجبارية"""
    __tablename__ = "required_channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(100), nullable=False, unique=True)
    channel_username = Column(String(100))
    channel_name = Column(String(200))
    is_active = Column(Boolean, default=True)
