import logging
import json
import time
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger("intentgate.redis")

class InMemoryRedisMock:
    """In-memory Redis fallback if Redis service is unreachable during standalone execution."""
    def __init__(self):
        self._store = {}
        self._locks = {}

    async def get(self, name: str) -> Optional[str]:
        item = self._store.get(name)
        if item is None:
            return None
        val, expiry = item
        if expiry and time.time() > expiry:
            del self._store[name]
            return None
        return val

    async def set(self, name: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        if nx and name in self._store:
            existing_val, expiry = self._store[name]
            if not expiry or time.time() <= expiry:
                return False
        
        expiry_time = time.time() + ex if ex else None
        self._store[name] = (str(value), expiry_time)
        return True

    async def incrby(self, name: str, amount: int = 1) -> int:
        val = await self.get(name)
        curr = int(val) if val else 0
        new_val = curr + amount
        await self.set(name, str(new_val))
        return new_val

    async def delete(self, *names: str) -> int:
        count = 0
        for n in names:
            if n in self._store:
                del self._store[n]
                count += 1
        return count

    async def exists(self, name: str) -> bool:
        val = await self.get(name)
        return val is not None

    async def lock(self, name: str, timeout: int = 10):
        class LockContext:
            def __init__(self, parent, lock_name, lock_timeout):
                self.parent = parent
                self.lock_name = f"intentgate:lock:{lock_name}"
                self.lock_timeout = lock_timeout
                self.acquired = False

            async def __aenter__(self):
                acquired = await self.parent.set(self.lock_name, "1", ex=self.lock_timeout, nx=True)
                self.acquired = acquired
                return acquired

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if self.acquired:
                    await self.parent.delete(self.lock_name)

        return LockContext(self, name, timeout)

    async def ping(self) -> bool:
        return True


class RedisClientManager:
    """Manages Async Redis client with namespaces and graceful fallback."""
    def __init__(self):
        self._client = None
        self._is_mock = False

    async def init_redis(self):
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.ping()
            self._client = client
            self._is_mock = False
            logger.info("Connected to Redis server successfully at %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Redis connection failed (%s). Falling back to InMemoryRedisMock.", str(e))
            self._client = InMemoryRedisMock()
            self._is_mock = True

    @property
    def client(self):
        if self._client is None:
            self._client = InMemoryRedisMock()
            self._is_mock = True
        return self._client

    @property
    def is_mock(self) -> bool:
        return self._is_mock

redis_manager = RedisClientManager()
