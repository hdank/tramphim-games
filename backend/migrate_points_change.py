#!/usr/bin/env python3
"""
Migration script to add points_change column to match_history table
Run with: python migrate_points_change.py
"""

from sqlalchemy import text
from app.database import engine

def run_migration():
    with engine.connect() as connection:
        try:
            # SQLite: Add points_change column
            connection.execute(text("""
                ALTER TABLE match_history
                ADD COLUMN points_change INTEGER DEFAULT NULL
            """))
            print("✅ Added points_change column to match_history table")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️ points_change column already exists, skipping...")
            else:
                print(f"❌ Error adding points_change: {e}")
        
        connection.commit()
        print("✅ Migration completed successfully")

if __name__ == "__main__":
    run_migration()
