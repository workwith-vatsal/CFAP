from backend.app.core.config import settings


def get_password_reset_email_body(otp: str) -> str:
    """
    Generate the email body for a password-reset OTP.
    """

    return f"""\
Hello,

You have requested to reset your CFAP account password.

Your password reset OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request a password reset, you can safely ignore this email.
Your password will remain unchanged.

Regards,
CFAP Team
Cognitive Feedback Analytics Platform""".strip()


def get_verification_email_body(otp: str) -> str:
    """
    Generate the email body for an email-verification OTP.
    """

    return f"""\
Hello,

Your CFAP email verification OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request this verification, you can safely ignore this email.

Regards,
CFAP Team
Cognitive Feedback Analytics Platform""".strip()
