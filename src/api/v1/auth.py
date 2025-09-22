from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    status,
    BackgroundTasks,
    Request,
    Query,
    UploadFile, 
    File,
    Body,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi_limiter.depends import RateLimiter
from datetime import timedelta
from src.database.db import get_async_session
from src.schemas.users import (
    UserBaseSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserResponseSchema,
    UserUpdateSchema,
    UserUpdatePasswordSchema
)
from src.schemas.auth import RequestEmailSchema
from src.repository.users import UserRepository
from src.services.auth import AuthService, get_current_user
from src.database.models import UserModel
from src.services.cloudinary_service import UploadFileService
from src.settings import settings
from libgravatar import Gravatar
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get(
    "/me",
    response_model=UserResponseSchema,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    """
    Retrieves the current authenticated user's profile.

    This endpoint returns the details of the currently authenticated user.
    The rate limit is set to 10 requests per 60 seconds.

    :param current_user: The authenticated user object, injected by the dependency.
    :type current_user: UserModel
    :return: The user's profile information.
    :rtype: UserResponseSchema
    """
    return current_user


@router.post("/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def signup(
    body: UserCreateSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    auth_service: AuthService = Depends(AuthService)
):
    """
    Registers a new user and sends a confirmation email.

    This endpoint handles the user registration process. It checks for existing accounts,
    hashes the password, creates a new user, and schedules a background task to send a
    verification email.

    :param body: The user's registration data, including username, email, and password.
    :type body: UserCreateSchema
    :param background_tasks: FastAPI BackgroundTasks instance to run asynchronous tasks.
    :type background_tasks: BackgroundTasks
    :param request: The incoming request object.
    :type request: Request
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param auth_service: The authentication service instance for password hashing and token generation.
    :type auth_service: AuthService
    :raises HTTPException: If an account with the given email already exists.
    :return: The newly created user's data.
    :rtype: UserResponseSchema
    """
    user_repo = UserRepository(db)
    
    user = await user_repo.get_user_by_email(body.email)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )

    hashed_password = auth_service.hash_password(body.password)
    new_user = await user_repo.create_user(body, hashed_password)

    verification_token = auth_service.create_jwt_token({"email": body.email}, scope="verification_token")
    
    background_tasks.add_task(
        auth_service.send_confirmation_email, 
        new_user.email, 
        new_user.username, 
        str(request.base_url)
    )
    
    return new_user

@router.post("/login")
async def login(body: OAuth2PasswordRequestForm = Depends(), db=Depends(get_async_session)):
    """
    Authenticates a user and returns an access token.

    This endpoint validates user credentials and provides a JWT access token upon successful login.
    It checks for email confirmation and correct password.

    :param body: The login form data, containing username and password.
    :type body: OAuth2PasswordRequestForm
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: If the email is invalid, not confirmed, or the password is incorrect.
    :return: A dictionary containing the access token.
    :rtype: dict
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(body.username)
    auth_service = AuthService()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email is not verified"
        )
    if not auth_service.verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    access_token = auth_service.create_jwt_token(
        payload={"email": user.email}
    )

    auth_service.cache_user(user.email, user)
    
    return {"access_token": access_token}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db=Depends(get_async_session)):
    """
    Confirms a user's email address using a verification token.

    This endpoint verifies the token from the confirmation email and updates the user's
    status to "confirmed" in the database.

    :param token: The verification token received from the email.
    :type token: str
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: If the token is invalid or the user is not found.
    :return: A message confirming the email verification.
    :rtype: dict
    """
    user_repo = UserRepository(db)
    auth_service = AuthService()
    email = await auth_service.decode_verification_token(token)
    
    user = await user_repo.get_user_by_email(email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}

    await user_repo.change_confirmed_email(email)
    
    return {"message": "Email confirmed"}

@router.post("/request_email")
async def request_email(
    body: RequestEmailSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    auth_service: AuthService = Depends(AuthService)
):
    """
    Requests a new confirmation email for a user.

    This endpoint sends a new verification email to a user whose account is not yet
    confirmed. It prevents spamming by only sending an email if the account exists
    and is not already confirmed.

    :param body: The request body containing the user's email.
    :type body: RequestEmailSchema
    :param background_tasks: FastAPI BackgroundTasks instance to run asynchronous tasks.
    :type background_tasks: BackgroundTasks
    :param request: The incoming request object.
    :type request: Request
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param auth_service: The authentication service instance.
    :type auth_service: AuthService
    :raises HTTPException: If the user is not found or the email is already confirmed.
    :return: A message confirming that a new email has been sent.
    :rtype: dict
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(body.email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    if user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Email is already confirmed"
        )
    
    background_tasks.add_task(
        auth_service.send_confirmation_email,
        email=user.email,
        username=user.username,
        host=str(request.base_url)
    )
    
    return {"message": "New confirmation email sent"}



@router.post("/request_password_reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    body: RequestEmailSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Requests a password reset link to be sent to the user's email.
    
    This endpoint is designed to be secure against email enumeration attacks.
    It returns a success message regardless of whether the email exists,
    preventing attackers from validating email addresses.

    :param body: The request body containing the user's email.
    :type body: RequestEmailSchema
    :param background_tasks: FastAPI background tasks for asynchronous email sending.
    :type background_tasks: BackgroundTasks
    :param request: The incoming request object.
    :type request: Request
    :param db: The asynchronous database session dependency.
    :type db: AsyncSession
    :return: A dictionary with a success message.
    :rtype: dict
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(body.email)
    
    if user:
        auth_service = AuthService()
        reset_token = auth_service.create_jwt_token(
            {"email": user.email},
            scope="password_reset",
            expires_delta=10 
        )
        
        background_tasks.add_task(
            auth_service.send_password_reset_email,
            email=user.email,
            token=reset_token,
            host=str(request.base_url)
        )
    
    # Завжди повертаємо одну й ту ж відповідь, незалежно від того, чи знайдено користувача
    return {"message": "If a user with that email exists, a password reset link has been sent."}


@router.post("/reset_password/{token}")
async def reset_password(
    token: str,
    body: UserUpdatePasswordSchema,  
    db: AsyncSession = Depends(get_async_session)
):
    auth_service = AuthService()
    user_repo = UserRepository(db)

    try:
        email = auth_service.decode_jwt_token(token, scope="password_reset")
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token."
        )

    user = await user_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Використовуємо дані з моделі
    hashed_password = auth_service.hash_password(body.new_password)
    await user_repo.update_password(user, hashed_password)

    auth_service.redis_client.delete(f"user:{user.email}")

    return {"message": "Password has been successfully reset."}
