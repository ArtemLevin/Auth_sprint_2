import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from auth_service.app.db.session import get_db_session
from auth_service.app.schemas import LoginRequest, TokenPair, RegisterRequest
from auth_service.app.services.auth_service import AuthService
from schemas.auth import RefreshToken, MessageResponse
from schemas.error import SuccessResponse, ErrorResponseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=TokenPair)
async def login(
    request_data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.login(request_data.login, request_data.password)
    if not tokens:
        logger.warning("Неудачная попытка входа", login=request_data.login)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
        )

    logger.info("Пользователь успешно вошел в систему", login=request_data.login)
    return tokens


@router.post(
    "/register",
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully registered"},
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Login or email already exists",
            "model": ErrorResponseModel,
        },
    },
    summary="Register a new user",
    description="Registers a new user with provided login and password. Email is optional.",
)
async def register(
    request_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> Response:
    success, error_messages = await auth_service.register(
        request_data.login,
        request_data.password,
        request_data.email
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_messages,
        )

    logger.info("Пользователь успешно зарегистрировался", login=request_data.login)
    return Response(status_code=status.HTTP_201_CREATED)


@router.post(
    "/logout",
         response_model=MessageResponse,
         responses={200: {"model": MessageResponse, "description": "Logged out"}}
)
async def logout(
    request_data: RefreshToken, auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    await auth_service.logout(request_data.refresh_token)
    return Response(content={"message": "Logged out"},status_code=status.HTTP_200_OK)