from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models.database import get_db
from models.project import Project
from models.user import User
from api.routes.auth import get_current_active_user

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_language: str = "en"
    voice_settings: Optional[dict] = None
    video_settings: Optional[dict] = None
    illustration_style: Optional[str] = None
    target_platforms: Optional[List[str]] = None
    auto_publish: bool = False


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_language: str
    voice_settings: Optional[dict]
    video_settings: Optional[dict]
    illustration_style: Optional[str]
    target_platforms: Optional[List[str]]
    is_active: bool
    auto_publish: bool
    total_content_generated: int
    total_posts_published: int
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    db_project = Project(
        user_id=current_user.id,
        **project.dict()
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's projects."""
    projects = db.query(Project).filter(
        Project.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/activate")
async def activate_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Activate a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.is_active = True
    db.commit()
    return {"message": "Project activated successfully"}


@router.post("/{project_id}/deactivate")
async def deactivate_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.is_active = False
    db.commit()
    return {"message": "Project deactivated successfully"}


@router.get("/{project_id}/content")
async def get_project_content(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all content generated for a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    from models.content import GeneratedContent
    content = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id
    ).all()
    
    return content


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get project statistics."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    from models.content import GeneratedContent, ContentType, ContentStatus
    
    # Count content by type
    illustrations = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id,
        GeneratedContent.content_type == ContentType.ILLUSTRATION
    ).count()
    
    audio = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id,
        GeneratedContent.content_type == ContentType.AUDIO
    ).count()
    
    videos = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id,
        GeneratedContent.content_type == ContentType.VIDEO
    ).count()
    
    # Count by status
    completed = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id,
        GeneratedContent.status == ContentStatus.COMPLETED
    ).count()
    
    published = db.query(GeneratedContent).filter(
        GeneratedContent.project_id == project_id,
        GeneratedContent.is_published == True
    ).count()
    
    return {
        "project_id": project_id,
        "total_content": project.total_content_generated,
        "total_published": project.total_posts_published,
        "content_by_type": {
            "illustrations": illustrations,
            "audio": audio,
            "videos": videos
        },
        "content_by_status": {
            "completed": completed,
            "published": published
        }
    }
