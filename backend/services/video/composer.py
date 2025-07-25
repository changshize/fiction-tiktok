import asyncio
import tempfile
import os
from typing import Dict, Any, Optional, List
import ffmpeg
from PIL import Image, ImageDraw, ImageFont
import io
import uuid

from config.settings import settings


class VideoComposer:
    """Video composition service using FFmpeg."""
    
    def __init__(self):
        self.ffmpeg_path = settings.ffmpeg_path
    
    async def compose(
        self,
        image_data: bytes,
        audio_data: bytes,
        duration: float,
        resolution: str = "1080x1920",
        fps: int = 30
    ) -> Dict[str, Any]:
        """Compose video from image and audio."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save image and audio to temporary files
            image_path = os.path.join(temp_dir, "image.png")
            audio_path = os.path.join(temp_dir, "audio.mp3")
            output_path = os.path.join(temp_dir, "output.mp4")
            
            # Write files
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Parse resolution
            width, height = map(int, resolution.split('x'))
            
            # Resize image to match resolution
            resized_image_path = await self._resize_image(image_path, width, height, temp_dir)
            
            # Create video using FFmpeg
            try:
                (
                    ffmpeg
                    .input(resized_image_path, loop=1, t=duration, framerate=fps)
                    .output(
                        ffmpeg.input(audio_path),
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        pix_fmt='yuv420p',
                        shortest=None,
                        **{'b:v': '2M', 'b:a': '128k'}
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # Read output video
                with open(output_path, 'rb') as f:
                    video_data = f.read()
                
                return {
                    "video_data": video_data,
                    "duration": duration,
                    "resolution": resolution,
                    "fps": fps,
                    "format": "mp4"
                }
            
            except ffmpeg.Error as e:
                raise Exception(f"Video composition failed: {str(e)}")
    
    async def _resize_image(self, image_path: str, width: int, height: int, temp_dir: str) -> str:
        """Resize image to target resolution."""
        
        with Image.open(image_path) as img:
            # Calculate aspect ratios
            img_ratio = img.width / img.height
            target_ratio = width / height
            
            if img_ratio > target_ratio:
                # Image is wider, fit by height
                new_height = height
                new_width = int(height * img_ratio)
            else:
                # Image is taller, fit by width
                new_width = width
                new_height = int(width / img_ratio)
            
            # Resize image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create canvas with target size
            canvas = Image.new('RGB', (width, height), (0, 0, 0))
            
            # Center the resized image on canvas
            x_offset = (width - new_width) // 2
            y_offset = (height - new_height) // 2
            canvas.paste(resized_img, (x_offset, y_offset))
            
            # Save resized image
            resized_path = os.path.join(temp_dir, "resized_image.png")
            canvas.save(resized_path)
            
            return resized_path
    
    async def create_slideshow(
        self,
        images: List[bytes],
        audio_data: bytes,
        duration_per_image: float = 3.0,
        transition_duration: float = 0.5,
        resolution: str = "1080x1920"
    ) -> Dict[str, Any]:
        """Create slideshow video from multiple images."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save audio
            audio_path = os.path.join(temp_dir, "audio.mp3")
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Save and resize images
            image_paths = []
            width, height = map(int, resolution.split('x'))
            
            for i, image_data in enumerate(images):
                image_path = os.path.join(temp_dir, f"image_{i}.png")
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                resized_path = await self._resize_image(image_path, width, height, temp_dir)
                image_paths.append(resized_path)
            
            # Create video with transitions
            output_path = os.path.join(temp_dir, "slideshow.mp4")
            
            try:
                # Build FFmpeg filter for slideshow with crossfade transitions
                inputs = [ffmpeg.input(path, t=duration_per_image) for path in image_paths]
                
                if len(inputs) == 1:
                    # Single image
                    video = inputs[0]
                else:
                    # Multiple images with crossfade
                    video = inputs[0]
                    for i in range(1, len(inputs)):
                        video = ffmpeg.filter(
                            [video, inputs[i]],
                            'xfade',
                            transition='fade',
                            duration=transition_duration,
                            offset=duration_per_image - transition_duration
                        )
                
                # Combine with audio
                (
                    ffmpeg
                    .output(
                        video,
                        ffmpeg.input(audio_path),
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        pix_fmt='yuv420p',
                        shortest=None
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # Read output
                with open(output_path, 'rb') as f:
                    video_data = f.read()
                
                total_duration = len(images) * duration_per_image
                
                return {
                    "video_data": video_data,
                    "duration": total_duration,
                    "resolution": resolution,
                    "image_count": len(images),
                    "format": "mp4"
                }
            
            except ffmpeg.Error as e:
                raise Exception(f"Slideshow creation failed: {str(e)}")
    
    async def add_text_overlay(
        self,
        video_data: bytes,
        text: str,
        position: str = "bottom",
        font_size: int = 24,
        font_color: str = "white",
        background_color: str = "black",
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """Add text overlay to video."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.mp4")
            output_path = os.path.join(temp_dir, "output.mp4")
            
            # Save input video
            with open(input_path, 'wb') as f:
                f.write(video_data)
            
            # Position mapping
            position_map = {
                "top": "x=(w-text_w)/2:y=50",
                "bottom": "x=(w-text_w)/2:y=h-text_h-50",
                "center": "x=(w-text_w)/2:y=(h-text_h)/2",
                "top-left": "x=50:y=50",
                "top-right": "x=w-text_w-50:y=50",
                "bottom-left": "x=50:y=h-text_h-50",
                "bottom-right": "x=w-text_w-50:y=h-text_h-50"
            }
            
            pos = position_map.get(position, position_map["bottom"])
            
            try:
                # Add text overlay
                input_video = ffmpeg.input(input_path)
                
                video_with_text = ffmpeg.filter(
                    input_video,
                    'drawtext',
                    text=text,
                    fontsize=font_size,
                    fontcolor=font_color,
                    box=1,
                    boxcolor=f"{background_color}@0.5",
                    boxborderw=5,
                    **{pos.split(':')[0].split('=')[0]: pos.split(':')[0].split('=')[1],
                       pos.split(':')[1].split('=')[0]: pos.split(':')[1].split('=')[1]}
                )
                
                (
                    ffmpeg
                    .output(video_with_text, output_path)
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # Read output
                with open(output_path, 'rb') as f:
                    output_video_data = f.read()
                
                return {
                    "video_data": output_video_data,
                    "text_added": text,
                    "position": position,
                    "format": "mp4"
                }
            
            except ffmpeg.Error as e:
                raise Exception(f"Text overlay failed: {str(e)}")
    
    async def create_tiktok_format(
        self,
        image_data: bytes,
        audio_data: bytes,
        title: str,
        duration: float
    ) -> Dict[str, Any]:
        """Create TikTok-optimized video format."""
        
        # TikTok optimal settings
        resolution = "1080x1920"  # 9:16 aspect ratio
        fps = 30
        
        # Create base video
        video_result = await self.compose(
            image_data=image_data,
            audio_data=audio_data,
            duration=duration,
            resolution=resolution,
            fps=fps
        )
        
        # Add title overlay
        video_with_title = await self.add_text_overlay(
            video_data=video_result["video_data"],
            text=title,
            position="top",
            font_size=32,
            font_color="white",
            background_color="black"
        )
        
        return {
            "video_data": video_with_title["video_data"],
            "duration": duration,
            "resolution": resolution,
            "format": "mp4",
            "optimized_for": "tiktok",
            "title": title
        }
    
    async def get_video_info(self, video_data: bytes) -> Dict[str, Any]:
        """Get information about a video."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, "video.mp4")
            
            with open(video_path, 'wb') as f:
                f.write(video_data)
            
            try:
                probe = ffmpeg.probe(video_path)
                video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
                
                info = {
                    "duration": float(probe['format']['duration']),
                    "size": int(probe['format']['size']),
                    "format": probe['format']['format_name']
                }
                
                if video_stream:
                    info.update({
                        "width": int(video_stream['width']),
                        "height": int(video_stream['height']),
                        "fps": eval(video_stream['r_frame_rate']),
                        "video_codec": video_stream['codec_name']
                    })
                
                if audio_stream:
                    info.update({
                        "audio_codec": audio_stream['codec_name'],
                        "sample_rate": int(audio_stream['sample_rate']),
                        "channels": int(audio_stream['channels'])
                    })
                
                return info
            
            except ffmpeg.Error as e:
                raise Exception(f"Failed to get video info: {str(e)}")
