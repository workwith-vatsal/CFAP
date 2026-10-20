from fastapi import APIRouter, Depends, Response

from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.auth import MessageResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """
    Logout the current user. Clears the HttpOnly authentication cookie.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
    )

    return MessageResponse(
        message="Successfully logged out.",
    )
