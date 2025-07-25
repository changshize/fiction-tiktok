from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models.database import get_db
from models.novel import Novel, NovelChapter
from utils.novel_processor import NovelProcessor
from utils.scraper import NovelScraper

router = APIRouter()


# Pydantic models for request/response
class NovelCreate(BaseModel):
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    language: str = "en"
    source_url: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[str]] = None


class NovelResponse(BaseModel):
    id: int
    title: str
    author: Optional[str]
    description: Optional[str]
    language: str
    source_url: Optional[str]
    genre: Optional[str]
    tags: Optional[List[str]]
    total_chapters: int
    status: str
    
    class Config:
        from_attributes = True


class ChapterCreate(BaseModel):
    chapter_number: int
    title: Optional[str] = None
    content: str


class ChapterResponse(BaseModel):
    id: int
    chapter_number: int
    title: Optional[str]
    content: str
    word_count: int
    is_processed: bool
    
    class Config:
        from_attributes = True


@router.post("/", response_model=NovelResponse)
async def create_novel(novel: NovelCreate, db: Session = Depends(get_db)):
    """Create a new novel."""
    db_novel = Novel(**novel.dict())
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)
    return db_novel


@router.get("/", response_model=List[NovelResponse])
async def list_novels(
    skip: int = 0,
    limit: int = 100,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all novels with optional filtering."""
    query = db.query(Novel)
    
    if language:
        query = query.filter(Novel.language == language)
    
    novels = query.offset(skip).limit(limit).all()
    return novels


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(novel_id: int, db: Session = Depends(get_db)):
    """Get a specific novel by ID."""
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return novel


@router.put("/{novel_id}", response_model=NovelResponse)
async def update_novel(novel_id: int, novel_update: NovelCreate, db: Session = Depends(get_db)):
    """Update a novel."""
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    for field, value in novel_update.dict(exclude_unset=True).items():
        setattr(novel, field, value)
    
    db.commit()
    db.refresh(novel)
    return novel


@router.delete("/{novel_id}")
async def delete_novel(novel_id: int, db: Session = Depends(get_db)):
    """Delete a novel and all its chapters."""
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    db.delete(novel)
    db.commit()
    return {"message": "Novel deleted successfully"}


@router.post("/{novel_id}/chapters", response_model=ChapterResponse)
async def add_chapter(novel_id: int, chapter: ChapterCreate, db: Session = Depends(get_db)):
    """Add a chapter to a novel."""
    # Verify novel exists
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # Create chapter
    db_chapter = NovelChapter(
        novel_id=novel_id,
        **chapter.dict(),
        word_count=len(chapter.content.split())
    )
    db.add(db_chapter)
    
    # Update novel chapter count
    novel.total_chapters = db.query(NovelChapter).filter(NovelChapter.novel_id == novel_id).count() + 1
    
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


@router.get("/{novel_id}/chapters", response_model=List[ChapterResponse])
async def list_chapters(novel_id: int, db: Session = Depends(get_db)):
    """List all chapters for a novel."""
    chapters = db.query(NovelChapter).filter(NovelChapter.novel_id == novel_id).order_by(NovelChapter.chapter_number).all()
    return chapters


@router.post("/{novel_id}/upload")
async def upload_novel_file(
    novel_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a novel file and extract chapters."""
    # Verify novel exists
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Process the novel content
        processor = NovelProcessor()
        chapters = processor.extract_chapters(text_content)
        
        # Save chapters to database
        for i, chapter_content in enumerate(chapters, 1):
            db_chapter = NovelChapter(
                novel_id=novel_id,
                chapter_number=i,
                content=chapter_content,
                word_count=len(chapter_content.split())
            )
            db.add(db_chapter)
        
        # Update novel chapter count
        novel.total_chapters = len(chapters)
        db.commit()
        
        return {"message": f"Successfully uploaded {len(chapters)} chapters"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@router.post("/scrape")
async def scrape_novel(
    url: str = Form(...),
    language: str = Form("en"),
    db: Session = Depends(get_db)
):
    """Scrape a novel from a URL."""
    try:
        scraper = NovelScraper()
        novel_data = await scraper.scrape_novel(url, language)
        
        # Create novel in database
        db_novel = Novel(
            title=novel_data["title"],
            author=novel_data.get("author"),
            description=novel_data.get("description"),
            language=language,
            source_url=url,
            source_type="scraped",
            total_chapters=len(novel_data["chapters"])
        )
        db.add(db_novel)
        db.commit()
        db.refresh(db_novel)
        
        # Add chapters
        for i, chapter in enumerate(novel_data["chapters"], 1):
            db_chapter = NovelChapter(
                novel_id=db_novel.id,
                chapter_number=i,
                title=chapter.get("title"),
                content=chapter["content"],
                word_count=len(chapter["content"].split())
            )
            db.add(db_chapter)
        
        db.commit()
        
        return {
            "message": "Novel scraped successfully",
            "novel_id": db_novel.id,
            "chapters_count": len(novel_data["chapters"])
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error scraping novel: {str(e)}")
