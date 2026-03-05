import redis
import json
import os
from typing import Optional

# Connect to Redis using the URL from environment variables.
# decode_responses=True means Redis returns strings instead of bytes.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# How long cached data lives before Redis automatically deletes it (in seconds).
# After 5 minutes, the next request will go to the DB and refresh the cache.
CACHE_TTL = 300  # 5 minutes


def get_cached(key: str) -> Optional[dict]:
    """
    Try to get a value from Redis cache.
    Returns the parsed Python object, or None if not found.
    
    We wrap this in try/except because if Redis is down, we don't want
    the whole API to crash — we just fall back to the database.
    This is called the 'cache-aside' pattern: check cache first,
    fall back to DB on miss, then populate cache for next time.
    """
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        # Redis is unavailable — degrade gracefully, don't crash
        return None


def set_cached(key: str, value: dict, ttl: int = CACHE_TTL):
    """
    Store a value in Redis cache with an expiry time.
    json.dumps() converts the Python dict to a JSON string for storage.
    """
    try:
        redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass  # Cache write failed — not critical, continue without caching


def invalidate_cache(key: str):
    """
    Delete a cached value. Called when we update or delete a todo
    so the cache doesn't serve stale data.
    This is the hardest problem in caching — knowing when to invalidate.
    """
    try:
        redis_client.delete(key)
    except Exception:
        pass
