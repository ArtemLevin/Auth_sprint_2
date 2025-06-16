import aioredis
from app.settings import get_settings

settings = get_settings()

redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

async def get_redis_client() -> aioredis.Redis:
    return redis_client

async def test_connection():
    try:
        pong = await redis_client.ping()
        if pong:
            print("Подключение к Redis успешно")
    except Exception as e:
        print(f"Ошибка подключения к Redis: {e}")