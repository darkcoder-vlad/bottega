import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_PATH = os.getenv('DATABASE_PATH', 'bottega_hub/data/bottega.db')

# Ensure directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# SQLite connection string
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Use StaticPool for SQLite to avoid connection pool issues
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    poolclass=StaticPool,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session (for dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Get database session (direct call)"""
    return SessionLocal()


def init_db():
    """Initialize database tables"""
    from models import Base
    Base.metadata.create_all(bind=engine)
