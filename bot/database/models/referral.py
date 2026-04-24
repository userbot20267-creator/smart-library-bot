"""نموذج الإحالات"""
from sqlalchemy import Column, Integer, BigInteger, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base


class Referral(Base):
    """جدول الإحالات"""
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(BigInteger, nullable=False)  # المُحيل
    referred_id = Column(BigInteger, nullable=False)  # المُحال
    points_given = Column(Integer, default=50)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
