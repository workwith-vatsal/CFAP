from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import RegisterRequest
from backend.app.services.email_service import send_otp_email
from backend.app.services.otp_database import create_email_otp


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    if not data.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms and conditions.",
        )

    email = str(data.email).lower().strip()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    if data.mobile:
        existing_mobile = (
            db.query(User)
            .filter(User.mobile == data.mobile)
            .first()
        )

        if existing_mobile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this mobile number already exists.",
            )

    user = User(
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        mobile=data.mobile,
        email=email,
        password_hash=hash_password(data.password),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=False,
    )

    db.add(user)

    try:
        db.flush()

        otp = create_email_otp(
            db=db,
            user_id=user.id,
        )

        send_otp_email(
            recipient_email=user.email,
            otp=otp,
        )

        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to complete registration at this time. Please try again.",
        )

    return {
        "message": "Registration successful. A verification OTP has been sent to your email.",
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "mobile": user.mobile,
            "is_verified": user.is_verified,
        },
    }