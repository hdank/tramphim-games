from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class MatchStatus(str, enum.Enum):
    WIN = "WIN"
    LOSE = "LOSE"
    ABANDONED = "ABANDONED"
    PLAYING = "PLAYING"

class GameLevel(Base):
    __tablename__ = "game_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g. "Level 1", "Hard"
    card_count = Column(Integer, default=8) # Number of pairs
    time_limit = Column(Integer, nullable=True) # Seconds
    points_reward = Column(Integer, default=10)
    points_penalty = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    
    matches = relationship("MatchHistory", back_populates="level")

class CardImage(Base):
    __tablename__ = "card_images"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MatchHistory(Base):
    """
    Tracks every game session.
    Replaces old Game/PlayerStats models.
    """
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True, nullable=False)
    level_id = Column(Integer, ForeignKey("game_levels.id"))
    
    status = Column(Enum(MatchStatus), default=MatchStatus.PLAYING)
    score = Column(Integer, default=0)
    moves = Column(Integer, default=0)
    time_taken = Column(Float, default=0.0)
    flip_duration = Column(Float, default=0.6)  # Card flip-back duration (difficulty bonus)
    consecutive_wins = Column(Integer, default=0)  # Consecutive wins count at game start (for bonus calculation)
    consecutive_losses = Column(Integer, default=0)  # Tracks consecutive losses for resetting difficulty
    points_change = Column(Integer, nullable=True)  # Points awarded/deducted (None if still playing)
    
    # Game State for "Server is God" validation
    cards_state = Column(JSON) # The deck layout
    flipped_indices = Column(JSON, default=[]) # Currently flipped cards
    matched_pairs = Column(JSON, default=[]) # List of matched pair IDs
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    level = relationship("GameLevel", back_populates="matches")

# Keep GameSettings for global config if needed, or migrate to GameLevel
class GameSettings(Base):
    __tablename__ = "game_settings"
    id = Column(Integer, primary_key=True, index=True)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
