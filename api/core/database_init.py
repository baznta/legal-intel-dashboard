"""
Database initialization script.
"""

import asyncio
import structlog
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings

logger = structlog.get_logger()


async def create_tables():
    """Create all database tables."""
    try:
        # Create engine for initialization
        engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.debug,
            poolclass=None,  # Use default pool for initialization
        )
        
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from models.document import Base
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def drop_tables():
    """Drop all database tables (for testing)."""
    try:
        # Create engine for initialization
        engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.debug,
            poolclass=None,  # Use default pool for initialization
        )
        
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from models.document import Base
            
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
            
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


if __name__ == "__main__":
    """Run database initialization."""
    asyncio.run(create_tables()) 