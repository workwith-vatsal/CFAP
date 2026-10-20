from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a password before storing it in the database."""
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """Verify a plain password against its stored hash."""
    return pwd_context.verify(
        plain_password,
        password_hash,
    )


def create_access_token(
    subject: str,
    expires_minutes: int | None = None,
) -> str:
    """Create a JWT access token."""

    if expires_minutes is None:
        expires_minutes = settings.access_token_expire_minutes

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str | None:
    """Decode a JWT and return its subject."""

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        subject = payload.get("sub")

        if not subject:
            return None

        return str(subject)

    except JWTError:
        return None