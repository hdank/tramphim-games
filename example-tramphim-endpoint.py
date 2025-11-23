"""
Example tramphim backend endpoint to receive game results from Memory Card Game

Add this to: tramphim-backend/app/routers/minigame.py
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
import hmac
import hashlib
import json
import os
from datetime import datetime

router = APIRouter(prefix="/minigame", tags=["minigame"])

# Get secret from environment variable
WEBHOOK_SECRET = os.getenv("MINIGAME_WEBHOOK_SECRET", "your-secret-key-here")

def verify_webhook_signature(payload: dict, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature from game backend
    This ensures the webhook came from your game server, not a malicious source
    """
    message = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    expected = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("/game-result")
async def receive_game_result(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive game completion results
    
    Called automatically by Memory Game backend when a user completes a game
    """
    
    # Parse webhook payload
    payload = await request.json()
    signature = request.headers.get("X-Webhook-Signature", "")
    
    # Security: Verify signature
    if not verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Extract game data
    event = payload.get("event")
    timestamp = payload.get("timestamp")
    game_id = payload.get("game_id")
    data = payload.get("data", {})
    
    # Validate event type
    if event != "game_completed":
        return {"success": False, "message": "Unknown event type"}
    
    # Extract player data
    player_email = data.get("player_email")
    won = data.get("won")  # True if completed all matches
    score = data.get("score")
    moves = data.get("moves")
    time_taken = data.get("time_taken")
    matches_found = data.get("matches_found")
    
    # Find user in tramphim database
    user = db.query(User).filter(User.email == player_email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {player_email}")
    
    # Calculate points to award
    # You can customize this logic based on your requirements
    if won:
        if score >= 150:
            points_awarded = 20  # Excellent performance
        elif score >= 100:
            points_awarded = 15  # Good performance
        else:
            points_awarded = 10  # Completed
    else:
        points_awarded = 5  # Participation points
    
    # Option 1: Add game_points column to User model
    # First run: ALTER TABLE users ADD COLUMN game_points INTEGER DEFAULT 0;
    if hasattr(user, 'game_points'):
        user.game_points = (user.game_points or 0) + points_awarded
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": f"Awarded {points_awarded} points to {user.email}",
            "user_id": user.id,
            "points_awarded": points_awarded,
            "new_total_points": user.game_points
        }
    
    # Option 2: Create separate minigame_history table (recommended)
    # This keeps game history separate and doesn't modify User model
    
    # Uncomment this if you create MinigameHistory model:
    """
    from app.models.models import MinigameHistory
    
    history = MinigameHistory(
        user_id=user.id,
        game_type="memory_card",
        won=won,
        score=score,
        moves=moves,
        time_taken=time_taken,
        points_awarded=points_awarded,
        played_at=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    """
    
    # For now, just log the result
    print(f"[MINIGAME] User {user.email} (ID: {user.id}) earned {points_awarded} points")
    print(f"  Game ID: {game_id}, Won: {won}, Score: {score}, Time: {time_taken}s")
    
    return {
        "success": True,
        "message": f"Game result recorded for {user.email}",
        "user_id": user.id,
        "points_awarded": points_awarded
    }

# Optional: Add this model to tramphim-backend/app/models/models.py
"""
class MinigameHistory(Base):
    __tablename__ = "minigame_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    game_type = Column(String(50), default="memory_card")
    won = Column(Boolean)
    score = Column(Integer)
    moves = Column(Integer, nullable=True)
    time_taken = Column(Float, nullable=True)
    points_awarded = Column(Integer)
    played_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    user = relationship("User", backref="minigame_history")
"""
