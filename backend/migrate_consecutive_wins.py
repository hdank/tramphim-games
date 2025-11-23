#!/usr/bin/env python3
"""
Migration script to add consecutive_wins column to match_history table
Run with: python migrate_consecutive_wins.py
"""

from sqlalchemy import text
from app.database import engine

def run_migration():
    with engine.connect() as connection:
        try:
            # SQLite: Add consecutive_wins column
            connection.execute(text("""
                ALTER TABLE match_history
                ADD COLUMN consecutive_wins INTEGER DEFAULT 0
            """))
            print("✅ Added consecutive_wins column to match_history table")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️ consecutive_wins column already exists, skipping...")
            else:
                print(f"❌ Error adding consecutive_wins: {e}")
        
        connection.commit()
        print("✅ Migration completed successfully")

if __name__ == "__main__":
    run_migration()
