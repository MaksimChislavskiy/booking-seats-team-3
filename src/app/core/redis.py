from redis.asyncio import Redis

from app.core.config import settings

redis: Redis | None = None


async def get_redis() -> Redis:
    """Возвращает инициализированный Redis-клиент."""
    if redis is None:
        raise RuntimeError('Redis is not initialized')
    return redis


async def init_redis() -> None:
    """Инициализирует подключение к Redis."""
    global redis
    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
    )


async def close_redis() -> None:
    """Закрывает подключение к Redis."""
    if redis:
        await redis.close()
