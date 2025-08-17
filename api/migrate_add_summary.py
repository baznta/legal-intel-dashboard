#!/usr/bin/env python3
"""
Migration script to add summary field to document_metadata table.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate_database():
    """Add summary field to document_metadata table."""
    
    # Get database connection details from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://legal_user:legal_pass123@localhost:5432/legal_intel")
    
    # Parse connection string
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "")
    
    # Extract components
    if "@" in database_url:
        auth_part, rest = database_url.split("@", 1)
        if ":" in auth_part:
            user_part, password = auth_part.split(":", 1)
            username = user_part
        else:
            username = auth_part
            password = ""
    else:
        username = "legal_user"
        password = "legal_pass123"
    
    if ":" in rest:
        host_part, db_part = rest.split(":", 1)
        if "/" in db_part:
            port, database = db_part.split("/", 1)
        else:
            port = "5432"
            database = db_part
    else:
        host_part = rest
        port = "5432"
        database = "legal_intel"
    
    host = host_part
    
    print(f"🔧 Database Migration: Adding Summary Field")
    print(f"==========================================")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print("")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database
        )
        
        print("✅ Connected to database successfully")
        
        # Check if summary column already exists
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'document_metadata' 
        AND column_name = 'summary'
        """
        
        result = await conn.fetch(check_query)
        
        if result:
            print("✅ Summary column already exists")
        else:
            print("📝 Adding summary column to document_metadata table...")
            
            # Add summary column
            alter_query = """
            ALTER TABLE document_metadata 
            ADD COLUMN summary TEXT
            """
            
            await conn.execute(alter_query)
            print("✅ Summary column added successfully")
        
        # Verify the table structure
        print("\n📋 Current document_metadata table structure:")
        structure_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'document_metadata'
        ORDER BY ordinal_position
        """
        
        columns = await conn.fetch(structure_query)
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        await conn.close()
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n💡 Make sure:")
        print("   1. Database is running")
        print("   2. Environment variables are set correctly")
        print("   3. You have permission to alter the table")

if __name__ == "__main__":
    asyncio.run(migrate_database()) 