"""النموذج الأساسي"""
from sqlalchemy import create_engine, Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class TimestampMixin:
    """Mixin لإضافة timestamps تلقائية"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Database:
    """مدير قاعدة البيانات"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        # دعم Railway PostgreSQL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(
            database_url,
            poolclass=NullPool if "sqlite" in database_url else None,
            echo=False
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )

    def create_tables(self):
        """إنشاء الجداول"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("✅ تم إنشاء جداول قاعدة البيانات")

    @contextmanager
    def get_session(self) -> Session:
        """الحصول على session مع إدارة الأخطاء"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    def get_db(self):
        """Generator للـ dependency injection"""
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
