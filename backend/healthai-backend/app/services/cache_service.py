import json
import time
from typing import Any, Optional
import redis.asyncio as aioredis
from app.config import settings

_memory_cache: dict[str, tuple[Any, float]] = {}


class CacheService:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._use_memory = False

    async def connect(self) -> None:
        try:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await self._redis.ping()
        except Exception:
            self._redis = None
            self._use_memory = True

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.aclose()

    async def get(self, key: str) -> Optional[Any]:
        if self._use_memory or self._redis is None:
            entry = _memory_cache.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at > 0 and time.time() > expires_at:
                del _memory_cache[key]
                return None
            return value
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if self._use_memory or self._redis is None:
            expires_at = time.time() + ttl if ttl > 0 else 0
            _memory_cache[key] = (value, expires_at)
            return
        try:
            await self._redis.setex(key, ttl, json.dumps(value))
        except Exception:
            expires_at = time.time() + ttl if ttl > 0 else 0
            _memory_cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        _memory_cache.pop(key, None)
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None


cache_service = CacheService()
