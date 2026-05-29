import time
import redis.asyncio as aioredis
from fastapi import Request, HTTPException, status
from app.core.config import settings

# Ліміти: (кількість запитів, період в секундах)
RATE_LIMITS = {
    "anonymous": (2, 60),
    "authenticated": (10, 60),
}

# Redis клієнт (singleton)
redis_client: aioredis.Redis = None


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def rate_limit(request: Request, user_id: str | None):
    """
    Sliding time window rate limiter.
    - Авторизований юзер: ідентифікується по user_id, ліміт 10 req/хв
    - Анонімний юзер: ідентифікується по IP, ліміт 2 req/хв
    """
    r = await get_redis()

    identity = user_id or request.client.host
    limit_type = "authenticated" if user_id else "anonymous"
    limit, period = RATE_LIMITS[limit_type]

    key = f"rate_limit:{identity}"
    now = int(time.time())
    window_start = now - period

    # Видаляємо застарілі записи (старіші за period)
    await r.zremrangebyscore(key, min=0, max=window_start)

    # Рахуємо поточну кількість запитів у вікні
    request_count = await r.zcard(key)

    if request_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {limit} requests per minute.",
        )

    # Додаємо поточний запит в sorted set
    await r.zadd(key, {str(now): now})
    # Встановлюємо TTL щоб ключ сам видалявся
    await r.expire(key, period)
