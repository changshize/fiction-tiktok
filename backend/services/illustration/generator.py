import asyncio
import aiohttp
import base64
from typing import Dict, Any, Optional
import openai
from PIL import Image
import io
import json

from config.settings import settings
from utils.novel_processor import NovelProcessor


class IllustrationGenerator:
    """AI illustration generator using various APIs."""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.novel_processor = NovelProcessor()
    
    async def generate(
        self,
        prompt: str,
        style: str = "anime",
        size: str = "1024x1024",
        model: str = "dall-e-3"
    ) -> Dict[str, Any]:
        """Generate illustration from prompt."""
        
        if not self.openai_client:
            raise Exception("OpenAI API key not configured")
        
        try:
            # Enhance prompt with style
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            # Generate image using DALL-E
            response = await self.openai_client.images.generate(
                model=model,
                prompt=enhanced_prompt,
                size=size,
                quality="standard",
                n=1,
                response_format="b64_json"
            )
            
            # Get image data
            image_data = base64.b64decode(response.data[0].b64_json)
            
            return {
                "image_data": image_data,
                "model_used": model,
                "prompt_used": enhanced_prompt,
                "size": size
            }
        
        except Exception as e:
            # Fallback to Stable Diffusion if available
            if settings.stable_diffusion_api_key:
                return await self._generate_with_stable_diffusion(prompt, style, size)
            else:
                raise Exception(f"Image generation failed: {str(e)}")
    
    async def _generate_with_stable_diffusion(
        self,
        prompt: str,
        style: str,
        size: str
    ) -> Dict[str, Any]:
        """Generate image using Stable Diffusion API."""
        
        # This is a placeholder for Stable Diffusion API integration
        # You would implement the actual API calls here
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.stable_diffusion_api_key}",
        }
        
        # Convert size to width/height
        width, height = map(int, size.split('x'))
        
        data = {
            "text_prompts": [
                {
                    "text": self._enhance_prompt(prompt, style),
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise Exception(f"Stable Diffusion API error: {response.status}")
                
                result = await response.json()
                
                # Extract image data
                image_data = base64.b64decode(result["artifacts"][0]["base64"])
                
                return {
                    "image_data": image_data,
                    "model_used": "stable-diffusion-xl",
                    "prompt_used": self._enhance_prompt(prompt, style),
                    "size": size
                }
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt with style and quality modifiers."""
        
        style_modifiers = {
            "anime": "anime style, manga style, high quality, detailed, vibrant colors",
            "realistic": "photorealistic, high quality, detailed, professional photography",
            "fantasy": "fantasy art, magical, ethereal, detailed, high quality",
            "cyberpunk": "cyberpunk style, neon lights, futuristic, high tech, detailed",
            "watercolor": "watercolor painting, soft colors, artistic, traditional art",
            "oil_painting": "oil painting, classical art style, rich colors, detailed brushwork"
        }
        
        style_modifier = style_modifiers.get(style, style_modifiers["anime"])
        
        # Combine prompt with style
        enhanced_prompt = f"{prompt}, {style_modifier}"
        
        # Add quality enhancers
        quality_enhancers = [
            "masterpiece",
            "best quality",
            "highly detailed",
            "8k resolution"
        ]
        
        enhanced_prompt += ", " + ", ".join(quality_enhancers)
        
        return enhanced_prompt
    
    async def create_prompt_from_text(
        self,
        text: str,
        language: str = "en",
        params: Dict[str, Any] = None
    ) -> str:
        """Create illustration prompt from novel text."""
        
        if not params:
            params = {}
        
        # Extract scene descriptions
        scene_descriptions = self.novel_processor.extract_scene_descriptions(text)
        
        # Extract character descriptions
        character_descriptions = self.novel_processor.extract_character_descriptions(text)
        
        # Extract key phrases
        key_phrases = self.novel_processor.extract_key_phrases(text, language)
        
        # Build prompt
        prompt_parts = []
        
        # Add scene description if available
        if scene_descriptions:
            prompt_parts.append(scene_descriptions[0])
        
        # Add character descriptions
        if character_descriptions:
            for char in character_descriptions[:2]:  # Limit to 2 characters
                prompt_parts.append(char["description"])
        
        # Add key visual elements
        if key_phrases:
            visual_phrases = [phrase for phrase in key_phrases[:5] if self._is_visual_phrase(phrase)]
            if visual_phrases:
                prompt_parts.append(", ".join(visual_phrases))
        
        # Combine parts
        if prompt_parts:
            base_prompt = ". ".join(prompt_parts)
        else:
            # Fallback to text summary
            base_prompt = self.novel_processor.get_text_summary(text, 100)
        
        # Add context from parameters
        if params.get("mood"):
            base_prompt += f", {params['mood']} mood"
        
        if params.get("time_of_day"):
            base_prompt += f", {params['time_of_day']}"
        
        if params.get("setting"):
            base_prompt += f", {params['setting']} setting"
        
        return base_prompt
    
    def _is_visual_phrase(self, phrase: str) -> bool:
        """Check if a phrase is likely to be visually descriptive."""
        visual_keywords = [
            "color", "light", "dark", "bright", "beautiful", "large", "small",
            "tall", "short", "red", "blue", "green", "yellow", "black", "white",
            "golden", "silver", "shining", "glowing", "sparkling", "ancient",
            "modern", "old", "new", "magnificent", "elegant", "mysterious"
        ]
        
        return any(keyword in phrase.lower() for keyword in visual_keywords)
    
    async def generate_character_sheet(
        self,
        character_description: str,
        style: str = "anime"
    ) -> Dict[str, Any]:
        """Generate a character reference sheet."""
        
        prompt = f"character reference sheet, {character_description}, multiple poses, front view, side view, back view"
        
        return await self.generate(
            prompt=prompt,
            style=style,
            size="1024x1024"
        )
    
    async def generate_scene_illustration(
        self,
        scene_description: str,
        style: str = "anime",
        mood: str = "neutral"
    ) -> Dict[str, Any]:
        """Generate a scene illustration."""
        
        prompt = f"scene illustration, {scene_description}, {mood} atmosphere"
        
        return await self.generate(
            prompt=prompt,
            style=style,
            size="1920x1080"  # Landscape for scenes
        )
