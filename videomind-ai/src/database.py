"""
Database configuration and connection management.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_database():
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_directory_columns_sqlite():
    """Best-effort lightweight migration for new directory columns in SQLite."""
    if "sqlite" not in settings.database_url:
        return

    required = {
        "teaches_agent_to": "TEXT",
        "prompt_template": "TEXT",
        "execution_checklist": "TEXT",
        "agent_training_script": "TEXT",
    }

    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(directory_entries)"))
        existing = {row[1] for row in result.fetchall()}

        for col, col_type in required.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE directory_entries ADD COLUMN {col} {col_type}"))


def create_tables():
    """Create all database tables."""
    # Ensure model modules are imported so metadata includes all tables
    from models import VideoJob, DirectoryEntry  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_directory_columns_sqlite()
