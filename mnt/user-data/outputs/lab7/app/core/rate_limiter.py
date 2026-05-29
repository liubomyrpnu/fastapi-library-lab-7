import time
import redis.asyncio as aioredis
from fastapi import Request, HTTPException
from app.core.config import settings

# Ліміти: (max_requests, period_in_seconds)
RATE_LIMITS = {
    "anonymous": (2, 60),
    "authenticated": (10, 60),
}

# Redis клієнт (singleton)
redis_client: aioredis.Redis = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
)


async def rate_limit(request: Request, user_id: str | None) -> None:
    """Sliding window rate limiter.

    Для авторизованих: 10 запитів / хвилину (ідентифікація по user_id).
    Для анонімних:      2 запити  / хвилину (ідентифікація по IP).
    """
    identity = user_id or request.client.host
    limit_type = "authenticated" if user_id else "anonymous"
    limit, period = RATE_LIMITS[limit_type]

    key = f"rate_limit:{identity}"
    now = int(time.time())
    window_start = now - period

    # Видаляємо застарілі записи (старіші за period)
    await redis_client.zremrangebyscore(key, min=0, max=window_start)

    # Рахуємо поточну кількість запитів у вікні
    request_count = await redis_client.zcard(key)

    if request_count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit: {limit} requests per {period} seconds.",
        )

    # Додаємо поточний запит у вікно
    await redis_client.zadd(key, {str(now): now})
    # Встановлюємо TTL щоб ключ сам видалився
    await redis_client.expire(key, period)
