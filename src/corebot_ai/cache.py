"""Cache backends for retrieval and response reuse."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from functools import lru_cache

from redis import Redis
from redis.exceptions import RedisError

from corebot_ai.config import settings


class MemoryCache:
    """Simple in-memory cache with TTL."""

    def __init__(self) -> None:
        """Initialize empty in-memory cache."""
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> dict | None:
        """Return JSON-decoded value for key if present and not expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, payload = entry
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return json.loads(payload)

    def set(self, key: str, value: dict, ttl: int) -> None:
        """Store JSON-serializable value with TTL."""
        self._store[key] = (time.time() + ttl, json.dumps(value))


class RedisJsonCache:
    """Redis-backed JSON cache with graceful failure behavior."""

    def __init__(self, redis_url: str, fallback: MemoryCache) -> None:
        """Initialize Redis client and fallback cache."""
        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._fallback = fallback

    def _safe(self, fn: Callable[[], dict | None]) -> dict | None:
        """Execute Redis operation and fallback on connection errors."""
        try:
            return fn()
        except RedisError:
            return None

    def get(self, key: str) -> dict | None:
        """Return JSON-decoded value by key."""
        payload = self._safe(lambda: self._client.get(key))
        if payload is None:
            return self._fallback.get(key)
        return json.loads(payload)

    def set(self, key: str, value: dict, ttl: int) -> None:
        """Store JSON-serializable value with TTL."""
        payload = json.dumps(value)
        ok = self._safe(lambda: self._client.setex(key, ttl, payload))
        if ok is None:
            self._fallback.set(key, value, ttl)


@lru_cache(maxsize=1)
def get_cache() -> RedisJsonCache | MemoryCache:
    """Return configured cache backend."""
    fallback = MemoryCache()
    if not settings.redis_url:
        return fallback
    return RedisJsonCache(settings.redis_url, fallback)
