import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_ipaddr

from auth_service.app.api.v1.routes import auth, roles
from auth_service.app.settings import settings
from auth_service.app.utils.cache import redis_client, test_connection
from auth_service.app.core.logging import setup_logging

logger = structlog.get_logger(__name__)

limiter = Limiter(
    key_func=get_ipaddr,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=settings.REDIS_URL.get_secret_value(),
)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(roles.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    setup_logging()
    logger.info("Приложение запускается...")
    await test_connection()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Приложение завершает работу...")
    await redis_client.close()
