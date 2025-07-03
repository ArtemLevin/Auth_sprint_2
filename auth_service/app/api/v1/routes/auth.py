from uuid import UUID

import structlog
from app.core.dependencies import get_current_user, rate_limit_dependency
from app.core.oauth import oauth
from app.db.session import get_db_session
from app.schemas import (LoginHistoryResponse, LoginRequest, RegisterRequest,
                         TokenPair)
from app.schemas.auth import MessageResponse, RefreshToken
from app.schemas.error import ErrorResponseModel
from app.services.auth_service import AuthService
from app.settings import settings
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse, Response

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/yandex/login", summary="Redirect to Yandex OAuth")
async def yandex_login(request: Request):
    return await oauth.yandex.authorize_redirect(request, settings.yandex_callback_url)

@router.get("/yandex/callback", summary="Yandex OAuth callback")
async def yandex_callback(
    request: Request,
    db_session=Depends(get_db_session),
):
    token = await oauth.yandex.authorize_access_token(request)
    profile = (await oauth.yandex.get("userinfo", token=token)).json()

    auth_service = AuthService(db_session)
    tokens = await auth_service.login_or_register_via_yandex(
        yandex_id=profile["id"],
        email=profile.get("default_email"),
        login=profile.get("login"),
    )

    redirect_url = (
        f"{settings.frontend_url}/auth?"
        f"access_token={tokens['access_token']}&"
        f"refresh_token={tokens['refresh_token']}"
    )
    return RedirectResponse(redirect_url)

async def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


@router.post(
    "/login",
    response_model=TokenPair,
    responses={
        status.HTTP_200_OK: {"model": TokenPair},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Incorrect login or password",
            "model": ErrorResponseModel,
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(lambda: rate_limit_dependency(traffic_type="login"))]
)
async def login(
    request_data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    tokens = await auth_service.login(
        request_data.login,
        request_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    if not tokens:
        logger.warning("Неудачная попытка входа", login=request_data.login)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponseModel(
                detail={"authentication": "Incorrect login or password"}
            ).model_dump(),
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
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    summary="Register a new user",
    description="Registers a new user with provided login and password. Email is optional.",
    dependencies=[Depends(lambda: rate_limit_dependency(traffic_type="register"))]
)
async def register(
    request_data: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
) -> Response:
    success, error_messages = await auth_service.register(
        request_data.login, request_data.password, request_data.email
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
    responses={200: {"model": MessageResponse, "description": "Logged out"}},
    summary="Log out from current session",
    description="Invalidates the provided refresh token, effectively logging out the user from this session.",
    dependencies=[Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def logout(
    request_data: RefreshToken, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    await auth_service.logout(request_data.refresh_token)
    return MessageResponse(message="Logged out")


@router.post(
    "/refresh",
    response_model=TokenPair,
    responses={
        status.HTTP_200_OK: {"model": TokenPair},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token",
            "model": ErrorResponseModel,
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    summary="Refresh access token",
    description="Exchanges a valid refresh token for a new access token and refresh token.",
    dependencies=[Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def refresh_token(
    request_data: RefreshToken,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    try:
        new_tokens = await auth_service.refresh_tokens(request_data.refresh_token)
        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponseModel(
                    detail={"token": "Invalid or expired refresh token"}
                ).model_dump(),
            )
        return new_tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponseModel(
                detail={"token": str(e)}
            ).model_dump(),
        )

@router.post(
    "/logout_all_other_sessions",
    response_model=MessageResponse,
    responses={200: {"model": MessageResponse, "description": "Logged out from all other sessions"}},
    summary="Log out from all other active sessions",
    description="Invalidates all active sessions for the current user, except the one used for this request.",
    dependencies=[Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def logout_all_other_sessions_endpoint(
    request_data: RefreshToken,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    user_id = UUID(current_user["id"])
    await auth_service.logout_all_other_sessions(user_id, request_data.refresh_token)
    return MessageResponse(message="Logged out from all other sessions successfully")


@router.get(
    "/history",
    response_model=list[LoginHistoryResponse],
    summary="Get user login history",
    description="Retrieves the login history for the current authenticated user.",
    responses={
        status.HTTP_200_OK: {"description": "Login history retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def get_user_login_history(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of history entries to return"),
    offset: int = Query(0, ge=0, description="Number of history entries to skip"),
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> list[LoginHistoryResponse]:
    user_id = current_user["id"]
    history = await auth_service.get_login_history(user_id, limit=limit, offset=offset)
    return [LoginHistoryResponse.model_validate(entry) for entry in history]