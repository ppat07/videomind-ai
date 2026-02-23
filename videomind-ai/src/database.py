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


def _ensure_directory_columns():
    """Best-effort lightweight migration for new directory columns."""
    # Column definitions for missing columns
    required_columns = {
        "source_url": "TEXT",
        "content_type": "TEXT DEFAULT 'video'", 
        "article_content": "TEXT",
        "word_count": "INTEGER DEFAULT 0",
        "reading_time_minutes": "INTEGER DEFAULT 0",
        "teaches_agent_to": "TEXT",
        "prompt_template": "TEXT",
        "execution_checklist": "TEXT",
        "agent_training_script": "TEXT",
    }

    try:
        with engine.begin() as conn:
            if "sqlite" in settings.database_url:
                # SQLite approach
                result = conn.execute(text("PRAGMA table_info(directory_entries)"))
                existing = {row[1] for row in result.fetchall()}
            else:
                # PostgreSQL approach
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='directory_entries'
                """))
                existing = {row[0] for row in result.fetchall()}

            for col, col_def in required_columns.items():
                if col not in existing:
                    try:
                        conn.execute(text(f"ALTER TABLE directory_entries ADD COLUMN {col} {col_def}"))
                        print(f"✅ Added column: {col}")
                    except Exception as e:
                        print(f"⚠️ Could not add column {col}: {e}")
    except Exception as e:
        print(f"⚠️ Migration error: {e}")
        # Don't fail app startup for migration errors


def create_tables():
    """Create all database tables."""
    # Ensure model modules are imported so metadata includes all tables
    from models import VideoJob, DirectoryEntry  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_directory_columns()
