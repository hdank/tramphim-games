from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import asyncio
import copy

from .. import models, schemas
from ..database import get_db
from ..webhook_service import WebhookService
from ..game_logic import generate_cards

router = APIRouter(prefix="/game", tags=["game"])


def calculate_time_remaining(match: models.MatchHistory) -> int | None:
    """
    Calculate remaining time for a game in seconds.
    Returns None if no time limit or game is completed.
    """
    if match.status != models.MatchStatus.PLAYING:
        return None
    
    if not match.level or not match.level.time_limit:
        return None
    
    elapsed = (datetime.utcnow() - match.created_at).total_seconds()
    remaining = max(0, match.level.time_limit - elapsed)
    
    return int(remaining)

def calculate_effective_wins(player_email: str, level_id: int, db: Session) -> int:
    """
    Calculate 'Effective Wins' for hidden difficulty.
    Logic:
    1. Find the most recent block of 5 consecutive losses on this level.
    2. Count wins that occurred AFTER that block.
    3. If no such block exists, count all wins on this level.
    """
    # Get all completed games for this user on this level, ordered by most recent
    games = db.query(models.MatchHistory).filter(
        models.MatchHistory.user_email == player_email,
        models.MatchHistory.level_id == level_id,
        models.MatchHistory.status.in_([models.MatchStatus.WIN, models.MatchStatus.LOSE]),
        models.MatchHistory.completed_at != None
    ).order_by(desc(models.MatchHistory.completed_at)).all()

    if not games:
        return 0

    # Find the reset point (start of the last 5-loss streak)
    # We iterate backwards from most recent.
    # If we find 5 consecutive losses, everything before that (older) is ignored.
    
    consecutive_loss_counter = 0
    reset_index = -1 # Index in 'games' list where the 5-loss streak starts (most recent of the 5)

    for i, game in enumerate(games):
        if game.status == models.MatchStatus.LOSE:
            consecutive_loss_counter += 1
        else:
            consecutive_loss_counter = 0
        
        if consecutive_loss_counter >= 5:
            # Found a streak of 5 losses.
            # The games from 0 to i (inclusive) are the "current era".
            # Actually, if we just hit 5 losses, it means the user is currently in a "reset" state 
            # UNLESS they have won since then.
            # Wait, if we find 5 losses at indices k, k+1, k+2, k+3, k+4...
            # Then any game at index < k (more recent) counts towards the new streak.
            # So we stop looking further back.
            reset_index = i
            break
    
    # Calculate wins since the reset point
    effective_wins = 0
    
    # If we found a reset point, we only look at games more recent than that streak.
    # The streak ends at games[reset_index - 4] (the 1st loss of the 5) if we view chronologically,
    # but here 'games' is reversed (newest first).
    # So games[0] is newest. games[reset_index] is the 5th loss (oldest of the streak).
    # games[reset_index - 4] is the 1st loss (newest of the streak).
    # Any game with index < (reset_index - 4) occurred AFTER the streak.
    
    limit_index = len(games)
    if reset_index != -1:
        # The 5-loss streak is from index (reset_index-4) to reset_index.
        # We only count wins that happened AFTER this streak (index < reset_index - 4).
        limit_index = reset_index - 4
        if limit_index < 0:
            limit_index = 0

    for i in range(limit_index):
        if games[i].status == models.MatchStatus.WIN:
            effective_wins += 1
            
    return effective_wins

def calculate_flip_duration(consecutive_wins: int) -> float:
    """
    Calculate flip-back duration based on consecutive wins.
    Hidden difficulty: Activates at 2nd win (consecutive_wins >= 2)
    - 0-1 wins: 0.6s (base)
    - 2+ wins: 0.6s + 0.2s per win (max 10 wins -> 2.4s)
    """
    if consecutive_wins <= 1:
        return 0.6
    
    # Cap at 10 wins for calculation as per requirement (implied "up to 10 games")
    capped_wins = min(consecutive_wins, 10)
    
    # Each win after the first adds 0.2s
    # 2 wins: 0.6 + 0.12 = 0.72
    # 3 wins: 0.6 + 0.24 = 0.84
    # ...
    # 10 wins: 0.6 + 1.2 = 1.8
    difficulty_bonus = (capped_wins - 1) * 0.12
    return 0.6 + difficulty_bonus

def calculate_win_bonus(consecutive_wins: int) -> int:
    """
    Calculate Đậu point multiplier based on consecutive wins.
    If more than 1 consecutive win, double the rewards and penalties
    """
    return 2 if consecutive_wins > 1 else 1

# --- Game Endpoints ---

@router.get("/config", response_model=schemas.GameConfigResponse)
def get_game_config(db: Session = Depends(get_db)):
    """Get active levels and images for frontend"""
    levels = db.query(models.GameLevel).filter(models.GameLevel.is_active == True).all()
    images = db.query(models.CardImage).filter(models.CardImage.is_active == True).all()
    return {"levels": levels, "images": images}

@router.post("/start", response_model=schemas.MatchResponse)
def start_game(match_data: schemas.MatchCreate, db: Session = Depends(get_db)):
    """Start a new game session"""
    level = db.query(models.GameLevel).filter(models.GameLevel.id == match_data.level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Get effective wins to calculate difficulty
    consecutive_wins = calculate_effective_wins(match_data.player_email, level.id, db)
    flip_duration = calculate_flip_duration(consecutive_wins)
    
    images = db.query(models.CardImage).filter(models.CardImage.is_active == True).all()
    cards = generate_cards(level.card_count, images)
    
    new_match = models.MatchHistory(
        user_email=match_data.player_email,
        level_id=level.id,
        cards_state=cards,
        status=models.MatchStatus.PLAYING,
        score=0,
        moves=0,
        time_taken=0,
        flip_duration=flip_duration,
        consecutive_wins=consecutive_wins,  # Store for later use
        consecutive_losses=0 # Not strictly needed with new logic but good for record
    )
    
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    
    # Manually construct response to include time_remaining
    response = schemas.MatchResponse.from_orm(new_match)
    response.time_remaining = calculate_time_remaining(new_match)
    return response

@router.post("/{match_id}/flip", response_model=schemas.FlipCardResponse)
def flip_card(match_id: int, flip_req: schemas.FlipCardRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Handle card matching validation - cards are already flipped on frontend"""
    match = db.query(models.MatchHistory).filter(models.MatchHistory.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.status != models.MatchStatus.PLAYING:
        raise HTTPException(status_code=400, detail="Game is over")
    
    # Check time limit
    if match.level.time_limit:
        elapsed = (datetime.utcnow() - match.created_at).total_seconds()

        if elapsed > match.level.time_limit:
            match.status = models.MatchStatus.LOSE
            match.completed_at = datetime.utcnow()
            match.time_taken = elapsed
            
            # Calculate penalty for timeout
            # Use consecutive_wins stored at start for multiplier
            win_bonus_multiplier = calculate_win_bonus(match.consecutive_wins)
            penalty = match.level.points_penalty * win_bonus_multiplier
            match.points_change = -penalty
            
            db.commit()
            db.refresh(match)
            
            return {
                "match": schemas.MatchResponse.from_orm(match),
                "is_match": False,
                "message": "Time's up!"
            }
            
    
    cards = match.cards_state
    idx1 = flip_req.card_index_1
    idx2 = flip_req.card_index_2
    
    # Make a proper copy to work with
    cards = copy.deepcopy(cards)
    
    # Validate indices
    if idx1 < 0 or idx1 >= len(cards) or idx2 < 0 or idx2 >= len(cards):
        raise HTTPException(status_code=400, detail="Invalid card indices")
    
    if idx1 == idx2:
        raise HTTPException(status_code=400, detail="Cannot flip the same card twice")
    
    # Check if cards are already matched or invalid
    if cards[idx1]["matched"] or cards[idx2]["matched"]:
        raise HTTPException(status_code=400, detail="Card already matched")
    
    message = "No match"
    is_match = False
    
    # Check if cards match
    if cards[idx1]["value"] == cards[idx2]["value"]:
        # Use the consecutive wins stored at game start
        # If this game becomes a win, it will be consecutive_wins + 1
        # But for scoring DURING the game, we usually use the current multiplier?
        # Requirement: "Bonus x2 for win and will also lose x2"
        # This implies the multiplier applies to the whole game result.
        # For intermediate points (if any), let's apply it too.
        
        # NOTE: Requirement says "if the user have won more then 2 games consecutive... then it will send a trigger... Bonus x2"
        # This implies the bonus is active for the CURRENT game if the PREVIOUS games were wins.
        # So we use match.consecutive_wins to determine the multiplier.
        # Wait, "won more than 2 games consecutive... Bonus x2"
        # Does it mean > 2 (i.e. 3 wins) or >= 2?
        # Usually "won 2 games consecutive" means the 3rd game has the bonus.
        # My code uses > 1 (i.e. 2 wins) to activate.
        # Let's stick to: if you enter the game with a streak of 2+, you get the bonus.
        
        win_bonus_multiplier = calculate_win_bonus(match.consecutive_wins)
        
        # Match found!
        cards[idx1]["matched"] = True
        cards[idx1]["flipped"] = True  # Keep it flipped so it stays visible
        cards[idx2]["matched"] = True
        cards[idx2]["flipped"] = True  # Keep it flipped so it stays visible
        
        # Score update (optional, if we track score per move)
        # match.score += match.level.points_reward * win_bonus_multiplier 
        # Actually, score is usually calculated at the end or cumulative.
        # Let's keep it simple: Score is just for display, points are awarded at end.
        match.score += 10 * win_bonus_multiplier # Arbitrary in-game score
        
        is_match = True
        message = "Match found!"
        match.moves += 1
        
        # Check Win Condition
        matched_count = sum(1 for c in cards if c["matched"])
        if matched_count == len(cards):
            match.status = models.MatchStatus.WIN
            match.completed_at = datetime.utcnow()
            match.time_taken = (match.completed_at - match.created_at).total_seconds()
            message = "You Won!"
            
            # Calculate points awarded
            points_awarded = match.level.points_reward * win_bonus_multiplier
            match.points_change = points_awarded
            
            # Trigger Webhook using BackgroundTasks
            settings = db.query(models.GameSettings).first()
            if settings and settings.webhook_url:
                background_tasks.add_task(
                    WebhookService.send_game_result,
                    webhook_url=settings.webhook_url,
                    webhook_secret=settings.webhook_secret or "",
                    game_id=match.id,
                    player_email=match.user_email,
                    won=True,
                    score=match.score,
                    moves=match.moves,
                    time_taken=match.time_taken,
                    matches_found=matched_count // 2,
                    level_id=match.level.name,
                    points_change=points_awarded
                )
    else:
        # No match - reset flipped state for these cards
        win_bonus_multiplier = calculate_win_bonus(match.consecutive_wins)
        
        cards[idx1]["flipped"] = False
        cards[idx2]["flipped"] = False
        
        # Penalty in score (optional)
        match.score = max(0, match.score - 2 * win_bonus_multiplier)
        
        is_match = False
        message = "No match"
        match.moves += 1
    
    # Update the cards state with deepcopy to ensure SQLAlchemy detects changes
    match.cards_state = copy.deepcopy(cards)
    
    db.commit()
    db.refresh(match)
    
    # Construct response with time_remaining
    match_response = schemas.MatchResponse.from_orm(match)
    match_response.time_remaining = calculate_time_remaining(match)
    
    return {
        "match": match_response,
        "is_match": is_match,
        "message": message
    }

@router.post("/{match_id}/give-up")
def give_up_game(match_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    match = db.query(models.MatchHistory).filter(models.MatchHistory.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    match.status = models.MatchStatus.ABANDONED
    match.completed_at = datetime.utcnow()
    
    # Use points_penalty from level config
    win_bonus_multiplier = calculate_win_bonus(match.consecutive_wins)
    penalty = match.level.points_penalty * win_bonus_multiplier
    
    db.commit()
    
    # Trigger Webhook for giving up
    settings = db.query(models.GameSettings).first()
    if settings and settings.webhook_url:
        background_tasks.add_task(
            WebhookService.send_game_result,
            webhook_url=settings.webhook_url,
            webhook_secret=settings.webhook_secret or "",
            game_id=match.id,
            player_email=match.user_email,
            won=False,
            score=match.score,
            moves=match.moves,
            time_taken=0,
            matches_found=0,
            level_id=match.level.name,
            points_change=-penalty
        )
            
    return {"message": "Game abandoned"}
