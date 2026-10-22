from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_verified_user
from backend.app.core.security import hash_password, verify_password
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import ChangePasswordRequest, MessageResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Change password for the currently authenticated, verified user.
    Validates current password and updates to new password hash.
    """

    if current_user.auth_provider != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password change is not available for external OAuth accounts."
            ),
        )

    if not current_user.password_hash or not verify_password(
        data.current_password, current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password.",
        )

    current_user.password_hash = hash_password(data.new_password)
    db.commit()

    return MessageResponse(
        message="Password has been changed successfully.",
    )
