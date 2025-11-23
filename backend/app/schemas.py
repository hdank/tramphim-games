from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MatchStatus(str, Enum):
    WIN = "WIN"
    LOSE = "LOSE"
    ABANDONED = "ABANDONED"
    PLAYING = "PLAYING"

# --- Game Level Schemas ---
class GameLevelBase(BaseModel):
    name: str
    card_count: int
    time_limit: Optional[int] = None
    points_reward: int = 10
    points_penalty: int = 5
    is_active: bool = True

class GameLevelCreate(GameLevelBase):
    pass

class GameLevelUpdate(GameLevelBase):
    name: Optional[str] = None
    card_count: Optional[int] = None
    time_limit: Optional[int] = None
    points_reward: Optional[int] = None
    points_penalty: Optional[int] = None
    is_active: Optional[bool] = None

class GameLevelResponse(GameLevelBase):
    id: int
    
    class Config:
        from_attributes = True

# --- Card Image Schemas ---
class CardImageBase(BaseModel):
    url: str
    name: Optional[str] = None
    is_active: bool = True

class CardImageCreate(CardImageBase):
    pass

class CardImageResponse(CardImageBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Match Schemas ---
class MatchCreate(BaseModel):
    player_email: str
    level_id: int

class MatchResponse(BaseModel):
    id: int
    user_email: str
    level_id: int
    level: Optional[GameLevelResponse] = None
    status: MatchStatus
    score: int
    moves: int
    time_taken: float
    time_remaining: Optional[int] = None  # Seconds remaining, None if no limit or game ended
    flip_duration: float = 0.6  # Card flip-back duration in seconds (difficulty bonus)
    consecutive_wins: int = 0  # Consecutive wins at game start (for bonus calculation)
    points_change: Optional[int] = None  # Points awarded/deducted for this game (None if still playing)
    cards_state: Optional[List[Dict[str, Any]]] = None # The deck (hidden in some responses)
    flipped_indices: List[int]
    matched_pairs: List[int]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class FlipCardRequest(BaseModel):
    card_index_1: int
    card_index_2: int

class FlipCardResponse(BaseModel):
    match: MatchResponse
    is_match: Optional[bool]
    message: str
    
    class Config:
        from_attributes = True

# --- Admin Stats ---
class AdminStatsResponse(BaseModel):
    total_matches: int
    total_players: int
    avg_score: float
    recent_matches: List[MatchResponse]

# --- Config Response for Frontend ---
class GameConfigResponse(BaseModel):
    levels: List[GameLevelResponse]
    images: List[CardImageResponse]
