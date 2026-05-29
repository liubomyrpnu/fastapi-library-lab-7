"""
Юніт тести для rate limiter логіки.
Redis мокається через unittest.mock — реальне підключення не потрібне.

Тест кейси:
  1. Авторизований юзер — ще не досяг ліміту → 200
  2. Авторизований юзер — досяг ліміту (10 запитів) → 429
  3. Анонімний юзер — ще не досяг ліміту → 200
  4. Анонімний юзер — досяг ліміту (2 запити) → 429
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException


# ── Хелпер: створює фейковий Request з потрібним IP ──────────────────────────
def make_request(host: str = "127.0.0.1") -> MagicMock:
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = host
    return request


# ── Хелпер: патчить redis_client всередині rate_limiter ──────────────────────
def make_redis_mock(current_count: int) -> AsyncMock:
    """Повертає мок Redis де zcard повертає current_count."""
    mock = AsyncMock()
    mock.zremrangebyscore = AsyncMock()
    mock.zcard = AsyncMock(return_value=current_count)
    mock.zadd = AsyncMock()
    mock.expire = AsyncMock()
    return mock


# ═══════════════════════════════════════════════════════════════════════════════
# АВТОРИЗОВАНИЙ ЮЗЕР
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_authenticated_user_under_limit():
    """Авторизований юзер зробив 9 запитів → 10-й має пройти (200)."""
    redis_mock = make_redis_mock(current_count=9)  # 9 з 10 використано

    with patch("app.core.rate_limiter.redis_client", redis_mock):
        from app.core.rate_limiter import rate_limit

        request = make_request()
        # Не повинно кинути HTTPException
        await rate_limit(request, user_id="user_123")

        # Переконуємось що запит додано в Redis
        redis_mock.zadd.assert_called_once()
        redis_mock.expire.assert_called_once()


@pytest.mark.asyncio
async def test_authenticated_user_over_limit():
    """Авторизований юзер вже зробив 10 запитів → отримує 429."""
    redis_mock = make_redis_mock(current_count=10)  # ліміт вичерпано

    with patch("app.core.rate_limiter.redis_client", redis_mock):
        from app.core.rate_limiter import rate_limit

        request = make_request()
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(request, user_id="user_123")

        assert exc_info.value.status_code == 429
        # При 429 запит НЕ додається в Redis
        redis_mock.zadd.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# АНОНІМНИЙ ЮЗЕР
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_anonymous_user_under_limit():
    """Анонімний юзер зробив 1 запит → 2-й має пройти (200)."""
    redis_mock = make_redis_mock(current_count=1)  # 1 з 2 використано

    with patch("app.core.rate_limiter.redis_client", redis_mock):
        from app.core.rate_limiter import rate_limit

        request = make_request(host="192.168.1.1")
        # Не повинно кинути HTTPException
        await rate_limit(request, user_id=None)

        redis_mock.zadd.assert_called_once()
        redis_mock.expire.assert_called_once()


@pytest.mark.asyncio
async def test_anonymous_user_over_limit():
    """Анонімний юзер вже зробив 2 запити → отримує 429."""
    redis_mock = make_redis_mock(current_count=2)  # ліміт вичерпано

    with patch("app.core.rate_limiter.redis_client", redis_mock):
        from app.core.rate_limiter import rate_limit

        request = make_request(host="192.168.1.1")
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(request, user_id=None)

        assert exc_info.value.status_code == 429
        redis_mock.zadd.assert_not_called()
