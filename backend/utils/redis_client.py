import redis.asyncio as redis
from config.settings import settings
import json
from typing import Any, Optional
import pickle
from datetime import datetime


class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url, decode_responses=False)
    
    async def ping(self):
        """Test Redis connection."""
        return await self.redis.ping()
    
    async def close(self):
        """Close Redis connection."""
        await self.redis.close()
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set a key-value pair with optional expiration."""
        serialized_value = pickle.dumps(value)
        return await self.redis.set(key, serialized_value, ex=expire)
    
    async def get(self, key: str) -> Any:
        """Get a value by key."""
        value = await self.redis.get(key)
        if value is None:
            return None
        return pickle.loads(value)
    
    async def delete(self, key: str):
        """Delete a key."""
        return await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self.redis.exists(key))
    
    async def set_json(self, key: str, value: dict, expire: Optional[int] = None):
        """Set a JSON value."""
        json_value = json.dumps(value)
        return await self.redis.set(key, json_value, ex=expire)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get a JSON value."""
        value = await self.redis.get(key)
        if value is None:
            return None
        return json.loads(value.decode('utf-8'))
    
    async def lpush(self, key: str, *values):
        """Push values to the left of a list."""
        serialized_values = [pickle.dumps(v) for v in values]
        return await self.redis.lpush(key, *serialized_values)
    
    async def rpop(self, key: str) -> Any:
        """Pop a value from the right of a list."""
        value = await self.redis.rpop(key)
        if value is None:
            return None
        return pickle.loads(value)
    
    async def llen(self, key: str) -> int:
        """Get the length of a list."""
        return await self.redis.llen(key)
    
    async def publish(self, channel: str, message: Any):
        """Publish a message to a channel."""
        serialized_message = pickle.dumps(message)
        return await self.redis.publish(channel, serialized_message)
    
    async def subscribe(self, *channels):
        """Subscribe to channels."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
    
    async def set_task_status(self, task_id: str, status: str, result: Any = None, error: str = None):
        """Set task status for background jobs."""
        task_data = {
            "status": status,
            "result": result,
            "error": error,
            "timestamp": str(datetime.utcnow())
        }
        await self.set_json(f"task:{task_id}", task_data, expire=3600)  # 1 hour
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status."""
        return await self.get_json(f"task:{task_id}")
    
    async def cache_novel_content(self, novel_id: int, chapter_id: int, content: str, expire: int = 3600):
        """Cache novel content for faster access."""
        key = f"novel:{novel_id}:chapter:{chapter_id}"
        await self.set(key, content, expire=expire)
    
    async def get_cached_novel_content(self, novel_id: int, chapter_id: int) -> Optional[str]:
        """Get cached novel content."""
        key = f"novel:{novel_id}:chapter:{chapter_id}"
        return await self.get(key)
    
    async def cache_generated_content(self, content_id: int, file_path: str, expire: int = 86400):
        """Cache generated content metadata."""
        key = f"content:{content_id}"
        await self.set_json(key, {"file_path": file_path}, expire=expire)
    
    async def get_cached_content(self, content_id: int) -> Optional[dict]:
        """Get cached content metadata."""
        key = f"content:{content_id}"
        return await self.get_json(key)


# Global Redis client instance
redis_client = RedisClient()
