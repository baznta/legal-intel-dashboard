#!/usr/bin/env python3
"""
Management script for Legal Intel Dashboard API.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database_init import create_tables, drop_tables
from core.config import settings
import structlog

logger = structlog.get_logger()


async def main():
    """Main management function."""
    if len(sys.argv) < 2:
        print("Usage: python manage.py [create_tables|drop_tables|reset_tables]")
        print("  create_tables  - Create all database tables")
        print("  drop_tables    - Drop all database tables")
        print("  reset_tables   - Drop and recreate all tables")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "create_tables":
            print("Creating database tables...")
            await create_tables()
            print("✅ Database tables created successfully!")
            
        elif command == "drop_tables":
            print("Dropping database tables...")
            await drop_tables()
            print("✅ Database tables dropped successfully!")
            
        elif command == "reset_tables":
            print("Resetting database tables...")
            await drop_tables()
            await create_tables()
            print("✅ Database tables reset successfully!")
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: create_tables, drop_tables, reset_tables")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Management command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 