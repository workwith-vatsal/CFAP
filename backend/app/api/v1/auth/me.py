from fastapi import APIRouter, Depends

from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.auth import UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the authenticated user's profile.
    Requires a valid Bearer token.
    """

    return UserResponse.model_validate(current_user)
