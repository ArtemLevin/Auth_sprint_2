import aioredis
from auth_service.app.settings import settings

redis_client = aioredis.from_url(
    settings.REDIS_URL.get_secret_value(), decode_responses=True
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
