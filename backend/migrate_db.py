"""
Quick migration script to add webhook columns to existing database
Run this once to update your database schema
"""

import sqlite3
import os

db_path = "memory_game.db"

if not os.path.exists(db_path):
    print(f"Database {db_path} not found. It will be created when you start the server.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if columns already exist
cursor.execute("PRAGMA table_info(game_settings)")
columns = [row[1] for row in cursor.fetchall()]

print(f"Current columns in game_settings: {columns}")

# Add missing columns
columns_to_add = {
    'webhook_url': 'VARCHAR(500)',
    'webhook_secret': 'VARCHAR(255)',
    'points_per_win': 'INTEGER DEFAULT 10',
    'points_per_loss': 'INTEGER DEFAULT 2'
}

for column_name, column_type in columns_to_add.items():
    if column_name not in columns:
        try:
            sql = f"ALTER TABLE game_settings ADD COLUMN {column_name} {column_type}"
            cursor.execute(sql)
            print(f"✓ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            print(f"✗ Error adding {column_name}: {e}")
    else:
        print(f"- Column {column_name} already exists")

conn.commit()
conn.close()

print("\n✅ Migration complete! Restart your backend server.")
