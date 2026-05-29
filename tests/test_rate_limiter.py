import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.core.rate_limiter import rate_limit, RATE_LIMITS


def make_request(host: str = "127.0.0.1") -> MagicMock:
    """Створює мок Request з client.host."""
    request = MagicMock()
    request.client.host = host
    return request


def make_redis_mock(current_count: int) -> AsyncMock:
    """Створює мок Redis."""
    mock = AsyncMock()

    mock.zremrangebyscore = AsyncMock(return_value=None)
    mock.zcard = AsyncMock(return_value=current_count)
    mock.zadd = AsyncMock(return_value=None)
    mock.expire = AsyncMock(return_value=None)

    return mock


# ─────────────────────────────────────────────────────────────
# Авторизований юзер
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_authenticated_user_under_limit():
    """
    Авторизований юзер НЕ досяг ліміту
    (9 з 10) → 200
    """
    limit, _ = RATE_LIMITS["authenticated"]

    redis_mock = make_redis_mock(current_count=limit - 1)

    with patch(
        "app.core.rate_limiter.get_redis",
        new=AsyncMock(return_value=redis_mock)
    ):

        await rate_limit(
            make_request(),
            user_id="user_123"
        )

    redis_mock.zadd.assert_called_once()
    redis_mock.expire.assert_called_once()


@pytest.mark.asyncio
async def test_authenticated_user_over_limit():
    """
    Авторизований юзер ДОСЯГ ліміту
    (10 з 10) → 429
    """
    limit, _ = RATE_LIMITS["authenticated"]

    redis_mock = make_redis_mock(current_count=limit)

    with patch(
        "app.core.rate_limiter.get_redis",
        new=AsyncMock(return_value=redis_mock)
    ):

        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(
                make_request(),
                user_id="user_123"
            )

    assert exc_info.value.status_code == 429
    redis_mock.zadd.assert_not_called()


# ─────────────────────────────────────────────────────────────
# Анонімний юзер
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_anonymous_user_under_limit():
    """
    Анонімний юзер НЕ досяг ліміту
    (1 з 2) → 200
    """
    limit, _ = RATE_LIMITS["anonymous"]

    redis_mock = make_redis_mock(current_count=limit - 1)

    with patch(
        "app.core.rate_limiter.get_redis",
        new=AsyncMock(return_value=redis_mock)
    ):

        await rate_limit(
            make_request(host="192.168.1.1"),
            user_id=None
        )

    redis_mock.zadd.assert_called_once()
    redis_mock.expire.assert_called_once()


@pytest.mark.asyncio
async def test_anonymous_user_over_limit():
    """
    Анонімний юзер ДОСЯГ ліміту
    (2 з 2) → 429
    """
    limit, _ = RATE_LIMITS["anonymous"]

    redis_mock = make_redis_mock(current_count=limit)

    with patch(
        "app.core.rate_limiter.get_redis",
        new=AsyncMock(return_value=redis_mock)
    ):

        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(
                make_request(host="192.168.1.1"),
                user_id=None
            )

    assert exc_info.value.status_code == 429
    redis_mock.zadd.assert_not_called()