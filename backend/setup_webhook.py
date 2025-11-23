#!/usr/bin/env python3
"""
Setup Webhook Configuration for Memory Card Game
This script configures the webhook settings to send game results to tramphim-backend
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models

def setup_webhook():
    """Configure webhook settings for sending game results to tramphim"""
    db = SessionLocal()
    
    try:
        # Check if settings exist
        settings = db.query(models.GameSettings).first()
        
        # Configure webhook URL and secret
        # Use port 8003 for local development (tramphim-backend runs on port 8003)
        webhook_url = "http://localhost:8003/api/minigame/game-result"
        webhook_secret = os.getenv("MINIGAME_WEBHOOK_SECRET", "DF231f92h39H88H")
        
        if not settings:
            # Create new settings
            settings = models.GameSettings(
                webhook_url=webhook_url,
                webhook_secret=webhook_secret
            )
            db.add(settings)
            print("✅ Created new GameSettings")
        else:
            # Update existing settings
            settings.webhook_url = webhook_url
            settings.webhook_secret = webhook_secret
            print("✅ Updated existing GameSettings")
        
        db.commit()
        db.refresh(settings)
        
        print("\n" + "=" * 60)
        print("Webhook Configuration:")
        print("=" * 60)
        print(f"URL: {settings.webhook_url}")
        print(f"Secret: {settings.webhook_secret}")
        print("=" * 60)
        print("\n✅ Webhook setup complete!")
        
    except Exception as e:
        print(f"❌ Error setting up webhook: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    setup_webhook()
