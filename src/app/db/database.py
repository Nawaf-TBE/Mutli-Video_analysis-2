"""
Database configuration and session management for Multi-Video Analysis Platform.

This module provides:
- Database engine configuration with environment-specific settings
- Session management with proper connection pooling
- Database initialization and health checking
- Transaction management utilities
- Migration support preparation
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urlparse

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
class DatabaseConfig:
    """Database configuration class with environment-specific settings."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./video_analysis.db")
        self.echo_sql = os.getenv("DB_ECHO", "false").lower() == "true"
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
        
    @property
    def is_sqlite(self) -> bool:
        """Check if the database is SQLite."""
        return self.database_url.startswith("sqlite")
    
    @property
    def is_postgresql(self) -> bool:
        """Check if the database is PostgreSQL."""
        return self.database_url.startswith("postgresql")
    
    @property
    def is_mysql(self) -> bool:
        """Check if the database is MySQL."""
        return self.database_url.startswith("mysql")

# Initialize configuration
config = DatabaseConfig()

def create_database_engine() -> Engine:
    """
    Create and configure the database engine based on the database type.
    
    Returns:
        Engine: Configured SQLAlchemy engine
    """
    engine_kwargs = {
        "echo": config.echo_sql,
        "future": True,  # Use SQLAlchemy 2.0 style
    }
    
    if config.is_sqlite:
        # SQLite-specific configuration
        engine_kwargs.update({
            "connect_args": {
                "check_same_thread": False,
                "timeout": config.connect_timeout,
            },
            "poolclass": StaticPool,
        })
        logger.info(f"Configuring SQLite database: {config.database_url}")
        
    elif config.is_postgresql:
        # PostgreSQL-specific configuration
        engine_kwargs.update({
            "pool_size": config.pool_size,
            "max_overflow": config.max_overflow,
            "pool_timeout": config.pool_timeout,
            "pool_recycle": config.pool_recycle,
            "pool_pre_ping": True,  # Verify connections before use
        })
        logger.info("Configuring PostgreSQL database with connection pooling")
        
    elif config.is_mysql:
        # MySQL-specific configuration
        engine_kwargs.update({
            "pool_size": config.pool_size,
            "max_overflow": config.max_overflow,
            "pool_timeout": config.pool_timeout,
            "pool_recycle": config.pool_recycle,
            "pool_pre_ping": True,
        })
        logger.info("Configuring MySQL database with connection pooling")
    
else:
        # Generic configuration for other databases
        logger.warning(f"Using generic configuration for database: {config.database_url}")
    
    try:
        engine = create_engine(config.database_url, **engine_kwargs)
        
        # Add event listeners for better monitoring
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and integrity."""
            if config.is_sqlite:
                cursor = dbapi_connection.cursor()
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                # Set journal mode to WAL for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                # Set synchronous mode to NORMAL for better performance
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
        
        @event.listens_for(engine, "engine_connect")
        def log_connection(conn, branch):
            """Log database connections for monitoring."""
            logger.debug("Database connection established")
            
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise

# Create the engine
engine = create_database_engine()

# Create SessionLocal class with proper configuration
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Keep objects accessible after commit
)

# Create Base class for models
Base = declarative_base()

# Database session dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session for FastAPI endpoints.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function should be called during application startup.
    """
    try:
        # Import all models to ensure they are registered with Base
        from ..models import video, section, frame  # noqa: F401
        
        logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine) 
        logger.info("Database tables created successfully")
        
        # Verify database connection
        if check_db_health():
            logger.info("Database initialization completed successfully")
        else:
            logger.error("Database health check failed after initialization")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def check_db_health() -> bool:
    """
    Check database connectivity and health.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            # Execute a simple query to test connectivity
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def get_db_info() -> dict:
    """
    Get database information and statistics.
    
    Returns:
        dict: Database information including URL, engine details, and pool status
    """
    info = {
        "database_url": config.database_url,
        "database_type": "sqlite" if config.is_sqlite else "postgresql" if config.is_postgresql else "mysql" if config.is_mysql else "other",
        "echo_sql": config.echo_sql,
        "engine_name": engine.name,
        "driver": engine.driver,
    }
    
    # Add pool information for non-SQLite databases
    if not config.is_sqlite and hasattr(engine.pool, 'size'):
        info.update({
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "invalid": engine.pool.invalid(),
        })
    
    return info

def close_db_connections() -> None:
    """
    Close all database connections.
    
    This function should be called during application shutdown.
    """
    try:
        engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

# Transaction utilities
def execute_in_transaction(func, *args, **kwargs):
    """
    Execute a function within a database transaction.
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Any: Function return value
    """
    with get_db_session() as db:
        return func(db, *args, **kwargs)

# Database URL utilities
def parse_database_url(url: Optional[str] = None) -> dict:
    """
    Parse database URL into components.
    
    Args:
        url: Database URL to parse (defaults to current config)
        
    Returns:
        dict: Parsed URL components
    """
    url = url or config.database_url
    parsed = urlparse(url)
    
    return {
        "scheme": parsed.scheme,
        "username": parsed.username,
        "password": "***" if parsed.password else None,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "database": parsed.path.lstrip("/") if parsed.path else None,
    } 