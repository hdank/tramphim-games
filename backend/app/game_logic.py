import random
from typing import List, Dict, Any

# Fallback icons if no images provided
CARD_ICONS = [
    "🎮", "🎯", "🎲", "🎪", "🎨", "🎭", "🎪", "🎸",
    "⚽", "🏀", "🎾", "🏈", "⚾", "🎱", "🏐", "🏉",
    "🌟", "⭐", "✨", "💫", "🌙", "☀️", "🌈", "🔥",
    "🍎", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍒"
]

def generate_cards(card_count: int, images: List[Any] = None) -> List[Dict[str, Any]]:
    """
    Generate shuffled card deck for memory game.
    If images are provided, use them. Otherwise fallback to icons.
    """
    available_values = []
    
    if images and len(images) > 0:
        # Use uploaded images
        image_urls = [img.url for img in images]
        for i in range(card_count):
            available_values.append(image_urls[i % len(image_urls)])
    else:
        # Fallback to icons
        # Ensure we have enough icons
        icons_pool = CARD_ICONS * (card_count // len(CARD_ICONS) + 1)
        available_values = icons_pool[:card_count]
            
    deck = []
    # Create pairs
    for i in range(card_count):
        value = available_values[i]
        # Card 1
        deck.append({
            "id": i * 2,
            "value": value,
            "matched": False,
            "flipped": False,
            "type": "image" if images else "icon"
        })
        # Card 2
        deck.append({
            "id": i * 2 + 1,
            "value": value,
            "matched": False,
            "flipped": False,
            "type": "image" if images else "icon"
        })
        
    random.shuffle(deck)
    
    # Reassign sequential IDs after shuffle (optional, but good for frontend indexing)
    # Actually, keeping original pair IDs might be useful for debugging, 
    # but frontend usually needs index. Let's keep index as position.
    
    return deck

def calculate_score(moves: int, matches: int, settings: Dict[str, Any], time_taken: float = None) -> int:
    """Calculate final score based on performance"""
    # This might need to be adapted if we move scoring logic to database models
    # For now, we rely on the running score in the match object
    return 0
