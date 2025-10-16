"""
Database configuration and setup
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models.news import Base

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={'check_same_thread': False} if 'sqlite' in settings.DATABASE_URL else {},
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize database and create tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Verify database structure
        verify_database_structure()
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


def verify_database_structure():
    """Verify database structure"""
    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute("SELECT 1 FROM news LIMIT 1")
        db.close()
        logger.info("✅ Database structure verified")
    except Exception as e:
        logger.warning(f"⚠️ Database verification issue: {e}")
        logger.info("🔧 Recreating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables recreated successfully")


def get_db() -> Session:
    """
    Dependency for getting database session
    Use with FastAPI Depends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on import
init_database()