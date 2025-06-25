"""
Database connection and session management.
🔗 SQLAlchemy setup for configuration database.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from ..config.manager import get_app_config
from ..logging.logger import get_logger
from .models import Base

logger = get_logger(__name__)

# Global engine and session factory
engine = None
SessionLocal = None


def init_database():
    """Initialize database connection and create tables."""
    global engine, SessionLocal

    try:
        # Get database configuration
        config = get_app_config()
        database_url = config.database.url

        logger.info(f"Initializing database: {database_url.split('://')[0]}://...")

        # Create engine with configuration
        engine_kwargs = {
            "echo": config.database.echo_sql,
            "pool_pre_ping": True,
        }

        # SQLite-specific configuration
        if config.database.type.value == "sqlite":
            engine_kwargs["connect_args"] = {
                "check_same_thread": False,  # Allow multi-threading
                "timeout": config.database.pool_timeout,
            }
        else:
            # PostgreSQL/MySQL configuration
            engine_kwargs.update(
                {
                    "pool_size": config.database.pool_size,
                    "max_overflow": config.database.max_overflow,
                    "pool_timeout": config.database.pool_timeout,
                    "pool_recycle": config.database.pool_recycle,
                }
            )

        engine = create_engine(database_url, **engine_kwargs)

        # Enable SQLite-specific optimizations if using SQLite
        if config.database.type.value == "sqlite":

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

        logger.info(f"✅ Database initialized successfully")

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

    try:
        config = get_app_config()
        database_url = config.database.url

        # Extract database path from URL if it's SQLite
        if database_url.startswith("sqlite:///"):
            database_path = Path(database_url.replace("sqlite:///", ""))

            if backup_path is None:
                backup_path = database_path.with_suffix(
                    f".backup.{int(time.time())}.db"
                )

            if database_path.exists():
                shutil.copy2(database_path, backup_path)
                logger.info(f"📦 Database backed up to {backup_path}")
                return backup_path
            else:
                logger.warning("⚠️ No database file found to backup")
                return None
        else:
            logger.warning("⚠️ Database backup only supported for SQLite")
            return None
    except Exception as e:
        logger.error(f"❌ Database backup failed: {e}")
        return None
