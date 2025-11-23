"""
Quick database check and initialization script
"""
from app.database import engine, Base
from app import models

print("Checking database...")

# Create all tables
Base.metadata.create_all(bind=engine)

print("✓ Database tables created/verified")

# Check if tables exist
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\nTables in database: {tables}")

# Check game_settings columns
if 'game_settings' in tables:
    columns = [col['name'] for col in inspector.get_columns('game_settings')]
    print(f"\ngame_settings columns: {columns}")
    
    # Check if webhook columns exist
    required_cols = ['webhook_url', 'webhook_secret', 'points_per_win', 'points_per_loss']
    missing = [col for col in required_cols if col not in columns]
    
    if missing:
        print(f"\n⚠ Missing columns: {missing}")
        print("Run migrate_db.py to add them")
    else:
        print("\n✓ All required columns present")

print("\n✅ Database check complete!")
