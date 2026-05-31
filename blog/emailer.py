from email.message import EmailMessage
import smtplib
from typing import Optional
from .config import get_settings


def send_otp_email(recipient: str, code: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST is not configured")

    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = settings.smtp_from
    msg["To"] = recipient
    msg.set_content(f"Your verification code is: {code}\nThis code will expire shortly.")

    # Use STARTTLS if port is 587 (default) or if credentials provided
    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()

        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)

        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass
