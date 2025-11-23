#!/usr/bin/env python3
"""
Migration script to add difficulty tracking columns to match_history table
Run with: python migrate_difficulty.py
"""

from sqlalchemy import text
from app.database import engine

def run_migration():
    with engine.connect() as connection:
        try:
            # SQLite: Add columns one at a time with proper syntax
            # Check if columns exist and add them individually
            connection.execute(text("""
                ALTER TABLE match_history
                ADD COLUMN flip_duration FLOAT DEFAULT 0.6
            """))
            print("✅ Added flip_duration column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️ flip_duration column already exists, skipping...")
            else:
                print(f"❌ Error adding flip_duration: {e}")
        
        try:
            connection.execute(text("""
                ALTER TABLE match_history
                ADD COLUMN consecutive_losses INTEGER DEFAULT 0
            """))
            print("✅ Added consecutive_losses column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️ consecutive_losses column already exists, skipping...")
            else:
                print(f"❌ Error adding consecutive_losses: {e}")
        
        connection.commit()
        print("✅ Migration completed successfully")

if __name__ == "__main__":
    run_migration()
