#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for Memory Card Game

This script:
1. Reads all data from SQLite database
2. Creates the same schema in PostgreSQL
3. Migrates all data with proper type conversions
4. Validates data integrity

Requirements: pip install sqlalchemy psycopg2-binary

Usage:
    python migrate_sqlite_to_postgresql.py \
        --sqlite-db ./memory_game.db \
        --postgres-url "postgresql://memory_game_user:password@localhost:6432/memory_game_db"
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Load environment variables from .env file
load_dotenv()

# Import your models
sys.path.insert(0, str(Path(__file__).parent))
from app.models import Base, GameLevel, CardImage, MatchHistory, GameSettings, MatchStatus
from app.database import Base as DatabaseBase

def migrate_database(sqlite_url, postgres_url=None, backup_sqlite=True):
    """
    Migrate SQLite database to PostgreSQL
    
    Args:
        sqlite_url: SQLite database URL (e.g., "sqlite:///./memory_game.db")
        postgres_url: PostgreSQL connection URL (e.g., "postgresql://user:pass@host/db")
                     If None, will load from .env file
        backup_sqlite: Whether to backup SQLite file before migration
    """
    
    # Build PostgreSQL URL from .env if not provided
    if not postgres_url:
        db_user = os.getenv("DB_USER", "memory_game_user")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "6432")
        db_name = os.getenv("DB_NAME", "memory_game_db")
        
        if not db_password:
            print("Error: DB_PASSWORD not set in .env file")
            return False
        
        postgres_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print("=" * 70)
    print("SQLite to PostgreSQL Migration Script")
    print("=" * 70)
    print()
    
    # Backup SQLite if requested
    if backup_sqlite:
        print("[1/6] Creating SQLite backup...")
        import shutil
        sqlite_path = sqlite_url.replace("sqlite:///", "")
        backup_path = f"{sqlite_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if Path(sqlite_path).exists():
            shutil.copy2(sqlite_path, backup_path)
            print(f"      ✓ Backup created: {backup_path}")
        else:
            print(f"      ⚠ SQLite file not found: {sqlite_path}")
    print()
    
    # Connect to both databases
    print("[2/6] Connecting to databases...")
    sqlite_engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    postgres_engine = create_engine(
        postgres_url,
        echo=False,
        pool_pre_ping=True  # Check connection health
    )
    
    try:
        # Test connections
        with sqlite_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"      ✓ Connected to SQLite")
        
        with postgres_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"      ✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"      ✗ Connection failed: {e}")
        return False
    print()
    
    # Create schema in PostgreSQL
    print("[3/6] Creating PostgreSQL schema...")
    try:
        # Drop existing tables to avoid conflicts
        with postgres_engine.connect() as conn:
            inspector = inspect(conn)
            existing_tables = inspector.get_table_names()
            
            if existing_tables:
                print(f"      Found existing tables: {existing_tables}")
                response = input("      Drop existing tables? (yes/no): ").strip().lower()
                if response != 'yes':
                    print("      Migration cancelled.")
                    return False
                
                for table in ['match_history', 'card_images', 'game_levels', 'game_settings']:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                        conn.commit()
                    except Exception as e:
                        print(f"      Note: {table} - {e}")
        
        # Create all tables
        Base.metadata.create_all(postgres_engine)
        print("      ✓ Schema created successfully")
    except Exception as e:
        print(f"      ✗ Schema creation failed: {e}")
        return False
    print()
    
    # Migrate data
    print("[4/6] Migrating data...")
    
    sqlite_session = sessionmaker(bind=sqlite_engine)()
    postgres_session = sessionmaker(bind=postgres_engine)()
    
    try:
        # Migrate GameSettings (lowest dependency)
        settings = sqlite_session.query(GameSettings).all()
        if settings:
            for setting in settings:
                new_setting = GameSettings(
                    id=setting.id,
                    webhook_url=setting.webhook_url,
                    webhook_secret=setting.webhook_secret
                )
                postgres_session.add(new_setting)
            postgres_session.commit()
            print(f"      ✓ Migrated {len(settings)} GameSettings records")
        
        # Migrate GameLevels
        levels = sqlite_session.query(GameLevel).all()
        if levels:
            level_map = {}
            for level in levels:
                new_level = GameLevel(
                    id=level.id,
                    name=level.name,
                    card_count=level.card_count,
                    time_limit=level.time_limit,
                    points_reward=level.points_reward,
                    points_penalty=level.points_penalty,
                    is_active=level.is_active
                )
                postgres_session.add(new_level)
                level_map[level.id] = new_level
            postgres_session.commit()
            print(f"      ✓ Migrated {len(levels)} GameLevel records")
        
        # Migrate CardImages
        images = sqlite_session.query(CardImage).all()
        if images:
            for image in images:
                new_image = CardImage(
                    id=image.id,
                    url=image.url,
                    name=image.name,
                    is_active=image.is_active,
                    created_at=image.created_at or datetime.utcnow()
                )
                postgres_session.add(new_image)
            postgres_session.commit()
            print(f"      ✓ Migrated {len(images)} CardImage records")
        
        # Migrate MatchHistory (highest dependency)
        matches = sqlite_session.query(MatchHistory).all()
        if matches:
            for match in matches:
                new_match = MatchHistory(
                    id=match.id,
                    user_email=match.user_email,
                    level_id=match.level_id,
                    status=MatchStatus(match.status),
                    score=match.score,
                    moves=match.moves,
                    time_taken=match.time_taken,
                    flip_duration=match.flip_duration,
                    consecutive_wins=match.consecutive_wins,
                    consecutive_losses=match.consecutive_losses,
                    points_change=match.points_change,
                    cards_state=match.cards_state,
                    flipped_indices=match.flipped_indices or [],
                    matched_pairs=match.matched_pairs or [],
                    created_at=match.created_at or datetime.utcnow(),
                    completed_at=match.completed_at
                )
                postgres_session.add(new_match)
            postgres_session.commit()
            print(f"      ✓ Migrated {len(matches)} MatchHistory records")
        
        print("      ✓ All data migrated successfully")
    except Exception as e:
        print(f"      ✗ Data migration failed: {e}")
        postgres_session.rollback()
        sqlite_session.close()
        return False
    finally:
        sqlite_session.close()
        postgres_session.close()
    print()
    
    # Verify migration
    print("[5/6] Verifying data integrity...")
    sqlite_session = sessionmaker(bind=sqlite_engine)()
    postgres_session = sessionmaker(bind=postgres_engine)()
    
    try:
        sqlite_counts = {
            'game_settings': sqlite_session.query(GameSettings).count(),
            'game_levels': sqlite_session.query(GameLevel).count(),
            'card_images': sqlite_session.query(CardImage).count(),
            'match_history': sqlite_session.query(MatchHistory).count(),
        }
        
        postgres_counts = {
            'game_settings': postgres_session.query(GameSettings).count(),
            'game_levels': postgres_session.query(GameLevel).count(),
            'card_images': postgres_session.query(CardImage).count(),
            'match_history': postgres_session.query(MatchHistory).count(),
        }
        
        print("      Record counts:")
        all_match = True
        for table, sqlite_count in sqlite_counts.items():
            postgres_count = postgres_counts[table]
            match = "✓" if sqlite_count == postgres_count else "✗"
            print(f"        {match} {table}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
            if sqlite_count != postgres_count:
                all_match = False
        
        if not all_match:
            print("      ⚠ Record count mismatch detected!")
            response = input("      Continue anyway? (yes/no): ").strip().lower()
            if response != 'yes':
                return False
    except Exception as e:
        print(f"      ✗ Verification failed: {e}")
        return False
    finally:
        sqlite_session.close()
        postgres_session.close()
    print()
    
    # Final instructions
    print("[6/6] Migration complete!")
    print()
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Update your database.py connection string:")
    print("   SQLALCHEMY_DATABASE_URL = \"postgresql://user:password@localhost:6432/memory_game_db\"")
    print()
    print("2. Update requirements.txt by adding:")
    print("   psycopg2-binary==2.9.9")
    print()
    print("3. Run pip install to get the PostgreSQL driver:")
    print("   pip install -r requirements.txt")
    print()
    print("4. Test the connection:")
    print("   python -c \"from app.database import engine; engine.execute('SELECT 1')\"")
    print()
    print("5. Restart your application:")
    print("   systemctl restart memory-game-frontend")
    print()
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate Memory Game database from SQLite to PostgreSQL"
    )
    parser.add_argument(
        "--sqlite-db",
        default="./memory_game.db",
        help="Path to SQLite database file (default: ./memory_game.db)"
    )
    parser.add_argument(
        "--postgres-url",
        default=None,
        help="PostgreSQL connection URL (e.g., postgresql://user:pass@localhost:6432/db). If not provided, loads from .env"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip SQLite backup creation"
    )
    
    args = parser.parse_args()
    
    sqlite_url = f"sqlite:///{args.sqlite_db}"
    success = migrate_database(sqlite_url, args.postgres_url, backup_sqlite=not args.no_backup)
    
    sys.exit(0 if success else 1)
