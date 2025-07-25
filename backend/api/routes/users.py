from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from models.database import get_db
from models.user import User
from api.routes.auth import get_current_active_user, UserResponse

router = APIRouter()


class UserPreferences(BaseModel):
    default_language: str = "en"
    default_voice: str = "alloy"
    video_quality: str = "high"
    auto_publish: bool = False
    notification_settings: dict = {}


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only or own profile)."""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/{user_id}/preferences")
async def update_user_preferences(
    user_id: int,
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.preferences = preferences.dict()
    db.commit()
    
    return {"message": "Preferences updated successfully"}


@router.get("/{user_id}/preferences")
async def get_user_preferences(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user preferences."""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.preferences or {}


@router.put("/{user_id}/api-keys")
async def update_api_keys(
    user_id: int,
    api_keys: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user API keys (encrypted storage)."""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # TODO: Implement encryption for API keys
    user.api_keys = api_keys
    db.commit()
    
    return {"message": "API keys updated successfully"}


@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user statistics."""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user statistics
    from models.content import GeneratedContent
    from models.project import Project
    
    total_projects = db.query(Project).filter(Project.user_id == user_id).count()
    total_content = db.query(GeneratedContent).join(Project).filter(Project.user_id == user_id).count()
    
    return {
        "user_id": user_id,
        "total_projects": total_projects,
        "total_content_generated": total_content,
        "content_generated_count": user.content_generated_count,
        "last_login": user.last_login,
        "account_created": user.created_at
    }
