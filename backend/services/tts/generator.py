import asyncio
import aiohttp
from typing import Dict, Any, Optional
import openai
from elevenlabs import generate, set_api_key, voices
import io
import wave
import json

from config.settings import settings


class TTSGenerator:
    """Text-to-Speech generator supporting multiple providers."""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        
        # Initialize ElevenLabs if API key is available
        if settings.elevenlabs_api_key:
            set_api_key(settings.elevenlabs_api_key)
            self.elevenlabs_available = True
        else:
            self.elevenlabs_available = False
    
    async def generate(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
        speed: float = 1.0,
        provider: str = "auto"
    ) -> Dict[str, Any]:
        """Generate speech from text."""
        
        # Choose provider based on language and availability
        if provider == "auto":
            provider = self._choose_provider(language)
        
        if provider == "openai" and self.openai_client:
            return await self._generate_with_openai(text, voice, speed)
        elif provider == "elevenlabs" and self.elevenlabs_available:
            return await self._generate_with_elevenlabs(text, voice)
        else:
            raise Exception("No TTS provider available")
    
    def _choose_provider(self, language: str) -> str:
        """Choose the best provider for the given language."""
        
        # ElevenLabs is generally better for English
        if language == "en" and self.elevenlabs_available:
            return "elevenlabs"
        
        # OpenAI supports multiple languages well
        if self.openai_client:
            return "openai"
        
        # Fallback to ElevenLabs if available
        if self.elevenlabs_available:
            return "elevenlabs"
        
        raise Exception("No suitable TTS provider available")
    
    async def _generate_with_openai(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """Generate speech using OpenAI TTS."""
        
        # Default voice mapping
        voice_mapping = {
            "alloy": "alloy",
            "echo": "echo", 
            "fable": "fable",
            "onyx": "onyx",
            "nova": "nova",
            "shimmer": "shimmer"
        }
        
        selected_voice = voice_mapping.get(voice, "alloy")
        
        try:
            response = await self.openai_client.audio.speech.create(
                model="tts-1",
                voice=selected_voice,
                input=text,
                speed=speed
            )
            
            # Get audio data
            audio_data = b""
            async for chunk in response.iter_bytes():
                audio_data += chunk
            
            # Estimate duration (rough calculation)
            # Assuming average speaking rate of 150 words per minute
            word_count = len(text.split())
            duration = (word_count / 150) * 60 / speed
            
            return {
                "audio_data": audio_data,
                "duration": duration,
                "model_used": "openai-tts-1",
                "voice_used": selected_voice,
                "format": "mp3"
            }
        
        except Exception as e:
            raise Exception(f"OpenAI TTS generation failed: {str(e)}")
    
    async def _generate_with_elevenlabs(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate speech using ElevenLabs."""
        
        try:
            # Get available voices if none specified
            if not voice:
                voice = "Rachel"  # Default voice
            
            # Generate audio
            audio_data = generate(
                text=text,
                voice=voice,
                model="eleven_monolingual_v1"
            )
            
            # Convert to bytes if needed
            if hasattr(audio_data, 'read'):
                audio_data = audio_data.read()
            
            # Estimate duration
            word_count = len(text.split())
            duration = (word_count / 150) * 60  # 150 words per minute average
            
            return {
                "audio_data": audio_data,
                "duration": duration,
                "model_used": "elevenlabs-v1",
                "voice_used": voice,
                "format": "mp3"
            }
        
        except Exception as e:
            raise Exception(f"ElevenLabs TTS generation failed: {str(e)}")
    
    async def get_available_voices(self, provider: str = "auto") -> Dict[str, Any]:
        """Get list of available voices."""
        
        if provider == "auto":
            provider = "openai" if self.openai_client else "elevenlabs"
        
        if provider == "openai":
            return {
                "provider": "openai",
                "voices": [
                    {"id": "alloy", "name": "Alloy", "gender": "neutral"},
                    {"id": "echo", "name": "Echo", "gender": "male"},
                    {"id": "fable", "name": "Fable", "gender": "neutral"},
                    {"id": "onyx", "name": "Onyx", "gender": "male"},
                    {"id": "nova", "name": "Nova", "gender": "female"},
                    {"id": "shimmer", "name": "Shimmer", "gender": "female"}
                ]
            }
        
        elif provider == "elevenlabs" and self.elevenlabs_available:
            try:
                voice_list = voices()
                return {
                    "provider": "elevenlabs",
                    "voices": [
                        {
                            "id": voice.voice_id,
                            "name": voice.name,
                            "category": voice.category
                        }
                        for voice in voice_list
                    ]
                }
            except Exception as e:
                return {"provider": "elevenlabs", "voices": [], "error": str(e)}
        
        return {"provider": "none", "voices": []}
    
    async def generate_with_emotions(
        self,
        text: str,
        emotion: str = "neutral",
        language: str = "en",
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate speech with specific emotion (ElevenLabs only)."""
        
        if not self.elevenlabs_available:
            # Fallback to regular generation
            return await self.generate(text, language, voice)
        
        # Modify text to convey emotion (simple approach)
        emotion_prefixes = {
            "happy": "In a cheerful and upbeat tone: ",
            "sad": "In a melancholic and somber tone: ",
            "angry": "In an intense and forceful tone: ",
            "excited": "In an enthusiastic and energetic tone: ",
            "calm": "In a peaceful and serene tone: ",
            "mysterious": "In a mysterious and intriguing tone: "
        }
        
        if emotion in emotion_prefixes:
            modified_text = emotion_prefixes[emotion] + text
        else:
            modified_text = text
        
        return await self._generate_with_elevenlabs(modified_text, voice)
    
    async def generate_multilingual(
        self,
        text: str,
        language: str,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate speech for multiple languages."""
        
        # Language-specific voice recommendations
        language_voices = {
            "en": "alloy",
            "zh": "alloy",  # OpenAI supports Chinese
            "ja": "alloy",  # OpenAI supports Japanese
            "es": "nova",
            "fr": "shimmer",
            "de": "echo",
            "it": "fable",
            "pt": "onyx"
        }
        
        # Use language-specific voice if none provided
        if not voice and language in language_voices:
            voice = language_voices[language]
        
        return await self.generate(text, language, voice)
    
    async def split_and_generate(
        self,
        text: str,
        max_length: int = 4000,
        language: str = "en",
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Split long text and generate multiple audio segments."""
        
        # Split text into chunks
        chunks = self._split_text(text, max_length)
        
        audio_segments = []
        total_duration = 0
        
        for i, chunk in enumerate(chunks):
            result = await self.generate(chunk, language, voice)
            audio_segments.append({
                "index": i,
                "audio_data": result["audio_data"],
                "duration": result["duration"],
                "text": chunk
            })
            total_duration += result["duration"]
        
        return {
            "segments": audio_segments,
            "total_duration": total_duration,
            "total_segments": len(chunks),
            "model_used": audio_segments[0]["model_used"] if audio_segments else None
        }
    
    def _split_text(self, text: str, max_length: int) -> list:
        """Split text into chunks while preserving sentence boundaries."""
        
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
