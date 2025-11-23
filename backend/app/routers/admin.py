from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from pathlib import Path
import uuid

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("app/static/card_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Levels Management ---
@router.post("/levels", response_model=schemas.GameLevelResponse)
def create_level(level: schemas.GameLevelCreate, db: Session = Depends(get_db)):
    db_level = models.GameLevel(**level.dict())
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level

@router.get("/levels", response_model=List[schemas.GameLevelResponse])
def get_levels(db: Session = Depends(get_db)):
    return db.query(models.GameLevel).all()

@router.put("/levels/{level_id}", response_model=schemas.GameLevelResponse)
def update_level(level_id: int, level_update: schemas.GameLevelUpdate, db: Session = Depends(get_db)):
    db_level = db.query(models.GameLevel).filter(models.GameLevel.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    for key, value in level_update.dict(exclude_unset=True).items():
        setattr(db_level, key, value)
    
    db.commit()
    db.refresh(db_level)
    return db_level

@router.delete("/levels/{level_id}")
def delete_level(level_id: int, db: Session = Depends(get_db)):
    db_level = db.query(models.GameLevel).filter(models.GameLevel.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    db.delete(db_level)
    db.commit()
    return {"message": "Level deleted"}

# --- Images Management ---
@router.post("/images/upload")
async def upload_images(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload multiple image files for card images"""
    uploaded_images = []
    
    for file in files:
        # Validate file type
        if not file.content_type.startswith("image/"):
            continue
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create database record
        image_url = f"/static/card_images/{unique_filename}"
        db_image = models.CardImage(
            url=image_url,
            name=file.filename,
            is_active=True
        )
        db.add(db_image)
        uploaded_images.append({
            "filename": file.filename,
            "url": image_url
        })
    
    db.commit()
    return {
        "message": f"Uploaded {len(uploaded_images)} images",
        "images": uploaded_images
    }

@router.post("/images", response_model=schemas.CardImageResponse)
def create_image(image: schemas.CardImageCreate, db: Session = Depends(get_db)):
    """Create image by URL (legacy method)"""
    db_image = models.CardImage(**image.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@router.get("/images", response_model=List[schemas.CardImageResponse])
def get_images(db: Session = Depends(get_db)):
    return db.query(models.CardImage).all()

@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    db_image = db.query(models.CardImage).filter(models.CardImage.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete file if it's a local file
    if db_image.url.startswith("/static/"):
        file_path = Path("app") / db_image.url.lstrip("/")
        if file_path.exists():
            file_path.unlink()
    
    db.delete(db_image)
    db.commit()
    return {"message": "Image deleted"}

# --- Webhook Settings ---
@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    """Get webhook configuration"""
    settings = db.query(models.GameSettings).first()
    if not settings:
        # Create default settings
        settings = models.GameSettings(webhook_url="", webhook_secret="")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return {
        "webhook_url": settings.webhook_url or "",
        "webhook_secret": settings.webhook_secret or ""
    }

@router.put("/settings")
def update_settings(
    webhook_url: str = None,
    webhook_secret: str = None,
    db: Session = Depends(get_db)
):
    """Update webhook configuration"""
    settings = db.query(models.GameSettings).first()
    if not settings:
        settings = models.GameSettings()
        db.add(settings)
    
    if webhook_url is not None:
        settings.webhook_url = webhook_url
    if webhook_secret is not None:
        settings.webhook_secret = webhook_secret
    
    db.commit()
    db.refresh(settings)
    return {
        "message": "Settings updated",
        "webhook_url": settings.webhook_url,
        "webhook_secret": settings.webhook_secret
    }

# --- Stats ---
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_matches = db.query(models.MatchHistory).count()
    completed_matches = db.query(models.MatchHistory).filter(
        models.MatchHistory.status == models.MatchStatus.WIN
    ).count()
    
    return {
        "total_matches": total_matches,
        "completed_matches": completed_matches,
        "total_levels": db.query(models.GameLevel).count(),
        "total_images": db.query(models.CardImage).count()
    }


# --- Levels Management ---
@router.post("/levels", response_model=schemas.GameLevelResponse)
def create_level(level: schemas.GameLevelCreate, db: Session = Depends(get_db)):
    db_level = models.GameLevel(**level.dict())
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level

@router.get("/levels", response_model=List[schemas.GameLevelResponse])
def get_levels(db: Session = Depends(get_db)):
    return db.query(models.GameLevel).all()

@router.put("/levels/{level_id}", response_model=schemas.GameLevelResponse)
def update_level(level_id: int, level_update: schemas.GameLevelUpdate, db: Session = Depends(get_db)):
    db_level = db.query(models.GameLevel).filter(models.GameLevel.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    for key, value in level_update.dict(exclude_unset=True).items():
        setattr(db_level, key, value)
    
    db.commit()
    db.refresh(db_level)
    return db_level

@router.delete("/levels/{level_id}")
def delete_level(level_id: int, db: Session = Depends(get_db)):
    db_level = db.query(models.GameLevel).filter(models.GameLevel.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    db.delete(db_level)
    db.commit()
    return {"message": "Level deleted"}

# --- Images Management ---
@router.post("/images", response_model=schemas.CardImageResponse)
def create_image(image: schemas.CardImageCreate, db: Session = Depends(get_db)):
    db_image = models.CardImage(**image.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@router.get("/images", response_model=List[schemas.CardImageResponse])
def get_images(db: Session = Depends(get_db)):
    return db.query(models.CardImage).all()

@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    db_image = db.query(models.CardImage).filter(models.CardImage.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    db.delete(db_image)
    db.commit()
    return {"message": "Image deleted"}
