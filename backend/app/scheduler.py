"""
Background scheduler for game timeout enforcement and auto-fail mechanism.
Runs a periodic task every 5 seconds to check for games that have exceeded their time limit.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import httpx
import hmac
import hashlib
import json
from . import models
from .database import SessionLocal

logger = logging.getLogger(__name__)

scheduler = None


def send_webhook_sync(
    webhook_url: str,
    webhook_secret: str,
    game_id: int,
    player_email: str,
    won: bool,
    score: int,
    moves: int,
    time_taken: float,
    matches_found: int,
    level_id: str,
    points_change: int
) -> bool:
    """Synchronous wrapper for webhook sending (non-async)"""
    if not webhook_url or not webhook_secret:
        logger.warning("Webhook URL or secret not configured, skipping webhook")
        return False
    
    # Generate signature
    payload = {
        "event": "game_completed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "game_id": game_id,
        "data": {
            "player_email": player_email,
            "won": won,
            "score": score,
            "moves": moves,
            "time_taken": round(time_taken, 2),
            "matches_found": matches_found,
            "level_id": level_id,
            "points_change": points_change
        }
    }
    
    message = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    signature = hmac.new(
        webhook_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature
    }
    
    try:
        # Use synchronous httpx client
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Webhook sent successfully for game {game_id}")
                return True
            else:
                logger.error(
                    f"❌ Webhook failed for game {game_id}: "
                    f"Status {response.status_code}, Response: {response.text}"
                )
                return False
                
    except Exception as e:
        logger.error(f"❌ Error sending webhook for game {game_id}: {str(e)}")
        return False


def check_game_timeouts():
    """
    Background job that checks all active games and auto-fails those exceeding time limit.
    This ensures server-side enforcement even if user doesn't interact with the game.
    """
    db = SessionLocal()
    try:
        # Find all PLAYING games
        active_games = db.query(models.MatchHistory).filter(
            models.MatchHistory.status == models.MatchStatus.PLAYING
        ).all()
        
        current_time = datetime.utcnow()
        failed_games = []
        
        for game in active_games:
            if not game.level or not game.level.time_limit:
                # No time limit, skip this game
                continue
            
            elapsed = (current_time - game.created_at).total_seconds()
            
            # Check if time exceeded
            if elapsed > game.level.time_limit:
                # Auto-fail the game
                game.status = models.MatchStatus.LOSE
                game.completed_at = current_time
                game.time_taken = elapsed
                
                failed_games.append(game)
                logger.info(f"⏰ Auto-failed game {game.id} for {game.user_email} (timeout after {elapsed}s)")
        
        if failed_games:
            db.commit()
            
            # Send webhooks for all failed games
            settings = db.query(models.GameSettings).first()
            if settings and settings.webhook_url:
                for game in failed_games:
                    # Get fresh data after commit
                    db.refresh(game)
                    
                    # Calculate penalty with bonus multiplier
                    # Use the consecutive_wins stored at game start
                    win_bonus_multiplier = 2 if game.consecutive_wins > 1 else 1
                    penalty = (game.level.points_penalty if game.level else 0) * win_bonus_multiplier
                    
                    try:
                        send_webhook_sync(
                            webhook_url=settings.webhook_url,
                            webhook_secret=settings.webhook_secret or "",
                            game_id=game.id,
                            player_email=game.user_email,
                            won=False,
                            score=game.score,
                            moves=game.moves,
                            time_taken=game.time_taken,
                            matches_found=0,
                            level_id=game.level.name if game.level else "Unknown",
                            points_change=-penalty
                        )
                    except Exception as e:
                        logger.error(f"❌ Failed to send webhook for game {game.id}: {str(e)}")
            else:
                if not settings:
                    logger.warning("⚠️ No GameSettings configured, skipping webhooks for timeouts")
                else:
                    logger.warning("⚠️ No webhook URL configured, skipping webhooks for timeouts")
        
    except Exception as e:
        logger.error(f"❌ Error in check_game_timeouts: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler for game timeout enforcement.
    Should be called once at application startup.
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    scheduler = BackgroundScheduler(daemon=True)
    
    # Add job to check timeouts every 5 seconds
    scheduler.add_job(
        check_game_timeouts,
        'interval',
        seconds=5,
        id='check_game_timeouts',
        name='Check and auto-fail games on timeout',
        max_instances=1  # Prevent multiple instances running simultaneously
    )
    
    scheduler.start()
    logger.info("🚀 Game timeout scheduler started (checking every 5 seconds)")


def stop_scheduler():
    """
    Stop the background scheduler.
    Should be called when application shuts down.
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("🛑 Game timeout scheduler stopped")
