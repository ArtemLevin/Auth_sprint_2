import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_ipaddr

from app.api.v1.routes import auth, roles
from app.settings import settings
from app.utils.cache import redis_client, test_connection
from app.core.logging_config import setup_logging
from app.schemas.error import ErrorResponseModel

logger = structlog.get_logger(__name__)

limiter = Limiter(
    key_func=get_ipaddr,
    default_limits=[settings.rate_limit_default],
    storage_uri=settings.redis_url.get_secret_value(),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Приложение запускается...")
    await test_connection()
    yield
    logger.info("Приложение завершает работу...")
    await redis_client.close()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    docs_url=f"{settings.api_v1_str}/docs",
    redoc_url=f"{settings.api_v1_str}/redoc",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter

async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(
        "Превышен лимит запросов", ip_address=request.client.host, detail=exc.detail
    )
    error_detail = {"rate_limit": f"Rate limit exceeded: {exc.detail}"}
    return JSONResponse(
        content=ErrorResponseModel(detail=error_detail).model_dump(),
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(roles.router, prefix=settings.api_v1_str)
