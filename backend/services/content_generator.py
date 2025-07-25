import asyncio
from typing import Optional, Dict, Any
import os
from datetime import datetime
import uuid

from models.database import SessionLocal
from models.content import GeneratedContent, ContentStatus, ContentType
from models.novel import Novel, NovelChapter
from utils.redis_client import redis_client
from config.settings import settings

from .illustration.generator import IllustrationGenerator
from .tts.generator import TTSGenerator
from .video.composer import VideoComposer


class ContentGenerator:
    """Main content generation orchestrator."""
    
    def __init__(self):
        self.illustration_generator = IllustrationGenerator()
        self.tts_generator = TTSGenerator()
        self.video_composer = VideoComposer()
    
    async def generate_content(
        self,
        content_id: int,
        content_type: str,
        novel_id: int,
        chapter_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate content based on type."""
        db = SessionLocal()
        
        try:
            # Get content record
            content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
            if not content:
                raise Exception(f"Content {content_id} not found")
            
            # Update status to processing
            content.status = ContentStatus.PROCESSING
            db.commit()
            
            # Set task status in Redis
            await redis_client.set_task_status(
                f"content_{content_id}",
                "processing",
                {"content_id": content_id, "type": content_type}
            )
            
            # Get novel and chapter data
            novel = db.query(Novel).filter(Novel.id == novel_id).first()
            chapter = None
            if chapter_id:
                chapter = db.query(NovelChapter).filter(NovelChapter.id == chapter_id).first()
            
            if not novel:
                raise Exception(f"Novel {novel_id} not found")
            
            # Generate content based on type
            start_time = datetime.utcnow()
            result = None
            
            if content_type == ContentType.ILLUSTRATION.value:
                result = await self._generate_illustration(content, novel, chapter)
            elif content_type == ContentType.AUDIO.value:
                result = await self._generate_audio(content, novel, chapter)
            elif content_type == ContentType.VIDEO.value:
                result = await self._generate_video(content, novel, chapter)
            else:
                raise Exception(f"Unsupported content type: {content_type}")
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update content record
            content.status = ContentStatus.COMPLETED
            content.file_path = result.get("file_path")
            content.file_size = result.get("file_size")
            content.duration = result.get("duration")
            content.processing_time = int(processing_time)
            content.completed_at = datetime.utcnow()
            content.ai_model_used = result.get("model_used")
            
            db.commit()
            
            # Update task status in Redis
            await redis_client.set_task_status(
                f"content_{content_id}",
                "completed",
                result
            )
            
            return result
        
        except Exception as e:
            # Update content status to failed
            content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
            if content:
                content.status = ContentStatus.FAILED
                content.error_message = str(e)
                db.commit()
            
            # Update task status in Redis
            await redis_client.set_task_status(
                f"content_{content_id}",
                "failed",
                error=str(e)
            )
            
            raise e
        
        finally:
            db.close()
    
    async def _generate_illustration(
        self,
        content: GeneratedContent,
        novel: Novel,
        chapter: Optional[NovelChapter]
    ) -> Dict[str, Any]:
        """Generate illustration for novel content."""
        # Prepare prompt
        if content.prompt:
            prompt = content.prompt
        else:
            # Generate prompt from novel content
            text_content = chapter.content if chapter else novel.description or novel.title
            prompt = await self.illustration_generator.create_prompt_from_text(
                text_content,
                novel.language,
                content.generation_params or {}
            )
        
        # Generate illustration
        result = await self.illustration_generator.generate(
            prompt=prompt,
            style=content.generation_params.get("style", "anime") if content.generation_params else "anime",
            size=content.generation_params.get("size", "1024x1024") if content.generation_params else "1024x1024"
        )
        
        # Save file
        file_path = await self._save_generated_file(
            result["image_data"],
            f"illustration_{content.id}_{uuid.uuid4().hex[:8]}.png",
            "illustrations"
        )
        
        return {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "model_used": result["model_used"],
            "prompt_used": prompt
        }
    
    async def _generate_audio(
        self,
        content: GeneratedContent,
        novel: Novel,
        chapter: Optional[NovelChapter]
    ) -> Dict[str, Any]:
        """Generate audio narration for novel content."""
        # Get text content
        text_content = chapter.content if chapter else novel.description or novel.title
        
        if not text_content:
            raise Exception("No text content available for audio generation")
        
        # Generate audio
        result = await self.tts_generator.generate(
            text=text_content,
            language=novel.language,
            voice=content.generation_params.get("voice") if content.generation_params else None,
            speed=content.generation_params.get("speed", 1.0) if content.generation_params else 1.0
        )
        
        # Save file
        file_path = await self._save_generated_file(
            result["audio_data"],
            f"audio_{content.id}_{uuid.uuid4().hex[:8]}.mp3",
            "audio"
        )
        
        return {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "duration": result["duration"],
            "model_used": result["model_used"]
        }
    
    async def _generate_video(
        self,
        content: GeneratedContent,
        novel: Novel,
        chapter: Optional[NovelChapter]
    ) -> Dict[str, Any]:
        """Generate video combining illustration and audio."""
        # This requires both illustration and audio to be generated first
        # For now, we'll generate them on-the-fly
        
        text_content = chapter.content if chapter else novel.description or novel.title
        
        if not text_content:
            raise Exception("No text content available for video generation")
        
        # Generate illustration
        illustration_prompt = await self.illustration_generator.create_prompt_from_text(
            text_content,
            novel.language,
            content.generation_params or {}
        )
        
        illustration_result = await self.illustration_generator.generate(
            prompt=illustration_prompt,
            style=content.generation_params.get("style", "anime") if content.generation_params else "anime"
        )
        
        # Generate audio
        audio_result = await self.tts_generator.generate(
            text=text_content,
            language=novel.language,
            voice=content.generation_params.get("voice") if content.generation_params else None
        )
        
        # Compose video
        video_result = await self.video_composer.compose(
            image_data=illustration_result["image_data"],
            audio_data=audio_result["audio_data"],
            duration=audio_result["duration"],
            resolution=content.generation_params.get("resolution", "1080x1920") if content.generation_params else "1080x1920"
        )
        
        # Save file
        file_path = await self._save_generated_file(
            video_result["video_data"],
            f"video_{content.id}_{uuid.uuid4().hex[:8]}.mp4",
            "videos"
        )
        
        return {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "duration": video_result["duration"],
            "model_used": f"illustration: {illustration_result['model_used']}, audio: {audio_result['model_used']}"
        }
    
    async def _save_generated_file(self, data: bytes, filename: str, subfolder: str) -> str:
        """Save generated file to disk."""
        # Create directory if it doesn't exist
        directory = os.path.join(settings.upload_dir, subfolder)
        os.makedirs(directory, exist_ok=True)
        
        # Save file
        file_path = os.path.join(directory, filename)
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return file_path
    
    async def get_generation_status(self, content_id: int) -> Dict[str, Any]:
        """Get the status of content generation."""
        return await redis_client.get_task_status(f"content_{content_id}")
    
    async def cancel_generation(self, content_id: int) -> bool:
        """Cancel content generation (if possible)."""
        # Update status in Redis
        await redis_client.set_task_status(
            f"content_{content_id}",
            "cancelled"
        )
        
        # Update database
        db = SessionLocal()
        try:
            content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
            if content and content.status == ContentStatus.PROCESSING:
                content.status = ContentStatus.FAILED
                content.error_message = "Generation cancelled by user"
                db.commit()
                return True
        finally:
            db.close()
        
        return False
