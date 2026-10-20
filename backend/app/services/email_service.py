import smtplib
from email.message import EmailMessage

from backend.app.core.config import settings
from backend.app.services.email_templates import (
    get_password_reset_email_body,
    get_verification_email_body,
)


def _send_email(
    recipient_email: str,
    subject: str,
    body: str,
) -> None:
    """
    Internal helper — send a plain-text email via SMTP.
    """

    if not settings.smtp_host or not settings.smtp_username:
        raise RuntimeError(
            "SMTP configuration is missing. "
            "Configure SMTP_HOST and SMTP_USERNAME in .env."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email or settings.smtp_username
    message["To"] = recipient_email
    message.set_content(body)

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=30,
    ) as smtp:
        smtp.starttls()
        smtp.login(
            settings.smtp_username,
            settings.smtp_password,
        )
        smtp.send_message(message)


def send_otp_email(
    recipient_email: str,
    otp: str,
) -> None:
    """
    Send an email verification OTP.
    """

    _send_email(
        recipient_email=recipient_email,
        subject="CFAP Email Verification OTP",
        body=get_verification_email_body(otp),
    )


def send_password_reset_email(
    recipient_email: str,
    otp: str,
) -> None:
    """
    Send a password reset OTP.
    """

    _send_email(
        recipient_email=recipient_email,
        subject="CFAP Password Reset OTP",
        body=get_password_reset_email_body(otp),
    )