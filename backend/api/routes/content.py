from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from models.database import get_db
from models.content import GeneratedContent, ContentType, ContentStatus
from models.novel import Novel, NovelChapter
from services.content_generator import ContentGenerator

router = APIRouter()


class ContentTypeEnum(str, Enum):
    illustration = "illustration"
    audio = "audio"
    video = "video"
    social_post = "social_post"


class GenerateContentRequest(BaseModel):
    novel_id: int
    chapter_id: Optional[int] = None
    content_type: ContentTypeEnum
    prompt: Optional[str] = None
    generation_params: Optional[dict] = None


class ContentResponse(BaseModel):
    id: int
    novel_id: int
    chapter_id: Optional[int]
    content_type: str
    title: Optional[str]
    description: Optional[str]
    file_path: Optional[str]
    status: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate content (illustration, audio, video) from novel chapter."""
    # Verify novel exists
    novel = db.query(Novel).filter(Novel.id == request.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # Verify chapter exists if specified
    chapter = None
    if request.chapter_id:
        chapter = db.query(NovelChapter).filter(
            NovelChapter.id == request.chapter_id,
            NovelChapter.novel_id == request.novel_id
        ).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Create content record
    content = GeneratedContent(
        novel_id=request.novel_id,
        chapter_id=request.chapter_id,
        content_type=ContentType(request.content_type.value),
        prompt=request.prompt,
        generation_params=request.generation_params,
        status=ContentStatus.PENDING
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    
    # Start background generation task
    background_tasks.add_task(
        generate_content_task,
        content.id,
        request.content_type.value,
        novel.id,
        request.chapter_id
    )
    
    return content


@router.get("/", response_model=List[ContentResponse])
async def list_content(
    novel_id: Optional[int] = None,
    content_type: Optional[ContentTypeEnum] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List generated content with optional filtering."""
    query = db.query(GeneratedContent)
    
    if novel_id:
        query = query.filter(GeneratedContent.novel_id == novel_id)
    if content_type:
        query = query.filter(GeneratedContent.content_type == ContentType(content_type.value))
    if status:
        query = query.filter(GeneratedContent.status == ContentStatus(status))
    
    content = query.offset(skip).limit(limit).all()
    return content


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, db: Session = Depends(get_db)):
    """Get specific generated content by ID."""
    content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.delete("/{content_id}")
async def delete_content(content_id: int, db: Session = Depends(get_db)):
    """Delete generated content."""
    content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # TODO: Delete associated files
    
    db.delete(content)
    db.commit()
    return {"message": "Content deleted successfully"}


@router.post("/{content_id}/regenerate")
async def regenerate_content(
    content_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Regenerate existing content."""
    content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Reset status
    content.status = ContentStatus.PENDING
    content.error_message = None
    db.commit()
    
    # Start regeneration task
    background_tasks.add_task(
        generate_content_task,
        content.id,
        content.content_type.value,
        content.novel_id,
        content.chapter_id
    )
    
    return {"message": "Content regeneration started"}


@router.post("/batch-generate")
async def batch_generate_content(
    novel_id: int,
    content_types: List[ContentTypeEnum],
    background_tasks: BackgroundTasks,
    chapter_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Generate multiple types of content for a novel or specific chapters."""
    # Verify novel exists
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # Get chapters to process
    if chapter_ids:
        chapters = db.query(NovelChapter).filter(
            NovelChapter.novel_id == novel_id,
            NovelChapter.id.in_(chapter_ids)
        ).all()
    else:
        chapters = db.query(NovelChapter).filter(NovelChapter.novel_id == novel_id).all()
    
    generated_content = []
    
    for chapter in chapters:
        for content_type in content_types:
            # Create content record
            content = GeneratedContent(
                novel_id=novel_id,
                chapter_id=chapter.id,
                content_type=ContentType(content_type.value),
                status=ContentStatus.PENDING
            )
            db.add(content)
            generated_content.append(content)
    
    db.commit()
    
    # Start background generation tasks
    for content in generated_content:
        background_tasks.add_task(
            generate_content_task,
            content.id,
            content.content_type.value,
            content.novel_id,
            content.chapter_id
        )
    
    return {
        "message": f"Started generation of {len(generated_content)} content items",
        "content_ids": [c.id for c in generated_content]
    }


async def generate_content_task(content_id: int, content_type: str, novel_id: int, chapter_id: Optional[int]):
    """Background task to generate content."""
    try:
        generator = ContentGenerator()
        await generator.generate_content(content_id, content_type, novel_id, chapter_id)
    except Exception as e:
        # Update content status to failed
        from models.database import SessionLocal
        db = SessionLocal()
        content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
        if content:
            content.status = ContentStatus.FAILED
            content.error_message = str(e)
            db.commit()
        db.close()
