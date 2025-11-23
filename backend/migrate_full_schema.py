#!/usr/bin/env python3
"""
Complete migration script to create/update match_history table with all columns
Run with: python migrate_full_schema.py
"""

from sqlalchemy import text
from app.database import engine

def run_migration():
    with engine.connect() as connection:
        try:
            # Check if table exists
            result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='match_history'
            """))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                # Table exists, try to add missing columns
                try:
                    connection.execute(text("""
                        ALTER TABLE match_history
                        ADD COLUMN consecutive_wins INTEGER DEFAULT 0
                    """))
                    print("✅ Added consecutive_wins column")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        print("⚠️ consecutive_wins already exists")
                    else:
                        raise
                
                try:
                    connection.execute(text("""
                        ALTER TABLE match_history
                        ADD COLUMN flip_duration FLOAT DEFAULT 0.6
                    """))
                    print("✅ Added flip_duration column")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        print("⚠️ flip_duration already exists")
                    else:
                        raise
                        
            else:
                # Create new table with all columns
                print("Creating match_history table...")
                connection.execute(text("""
                    CREATE TABLE match_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email VARCHAR NOT NULL,
                        level_id INTEGER,
                        status VARCHAR DEFAULT 'PLAYING',
                        score INTEGER DEFAULT 0,
                        moves INTEGER DEFAULT 0,
                        time_taken FLOAT DEFAULT 0.0,
                        flip_duration FLOAT DEFAULT 0.6,
                        consecutive_wins INTEGER DEFAULT 0,
                        consecutive_losses INTEGER DEFAULT 0,
                        cards_state JSON,
                        flipped_indices JSON DEFAULT '[]',
                        matched_pairs JSON DEFAULT '[]',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        completed_at DATETIME,
                        FOREIGN KEY (level_id) REFERENCES game_levels(id)
                    )
                """))
                print("✅ Created match_history table with all columns")
            
            connection.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            connection.rollback()
            raise

if __name__ == "__main__":
    run_migration()
