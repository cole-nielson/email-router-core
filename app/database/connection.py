"""
Database connection and session management.
🔗 SQLAlchemy setup for configuration database.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = Path("data/email_router.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH.absolute()}"

# Global engine and session factory
engine = None
SessionLocal = None


def init_database():
    """Initialize database connection and create tables."""
    global engine, SessionLocal

    try:
        # Ensure data directory exists
        DATABASE_PATH.parent.mkdir(exist_ok=True)

        # Create engine with SQLite optimizations
        engine = create_engine(
            DATABASE_URL,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            connect_args={
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30,  # Connection timeout
            },
        )

        # Enable WAL mode for better concurrency
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        logger.info(f"✅ Database initialized at {DATABASE_PATH}")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def get_database_session() -> Session:
    """Get database session for dependency injection."""
    if SessionLocal is None:
        init_database()
        if SessionLocal is None:
             raise RuntimeError("Database not initialized, SessionLocal is None.")

    db = SessionLocal()
    if db is None:
        raise RuntimeError("Failed to create a database session.")
    return db


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    session = get_database_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to get a managed database session."""
    db = None
    try:
        db = get_database_session()
        yield db
    finally:
        if db:
            db.close()


def reset_database():
    """Reset database by dropping and recreating all tables."""
    global engine

    if engine is None:
        init_database()
        return

    logger.warning("🗑️ Dropping all database tables")
    Base.metadata.drop_all(bind=engine)

    logger.info("🏗️ Recreating database tables")
    Base.metadata.create_all(bind=engine)

    logger.info("✅ Database reset complete")


def backup_database(backup_path: Path = None):
    """Create database backup."""
    import shutil
    import time
    
    if backup_path is None:
        backup_path = DATABASE_PATH.with_suffix(f".backup.{int(time.time())}.db")

    if DATABASE_PATH.exists():
        shutil.copy2(DATABASE_PATH, backup_path)
        logger.info(f"📦 Database backed up to {backup_path}")
        return backup_path
    else:
        logger.warning("⚠️ No database file found to backup")
        return None
