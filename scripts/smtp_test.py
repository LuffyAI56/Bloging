"""
Simple SMTP test script to validate settings and optionally send a test email.
Usage:
    python scripts/smtp_test.py recipient@example.com

It imports `blog.config.get_settings()` so it will pick up `.env` values if present.
"""
import sys
from email.message import EmailMessage
import smtplib
import ssl

from blog.config import get_settings


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/smtp_test.py recipient@example.com")
        sys.exit(2)

    recipient = sys.argv[1]
    settings = get_settings()

    if not settings.smtp_host:
        print("SMTP_HOST is not configured. Set environment variables or .env first.")
        sys.exit(1)

    context = ssl.create_default_context()
    server = None
    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10, context=context)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()

        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)

        msg = EmailMessage()
        msg["Subject"] = "SMTP test from Bloging"
        msg["From"] = settings.smtp_from
        msg["To"] = recipient
        msg.set_content("This is a test message sent by scripts/smtp_test.py")

        server.send_message(msg)
        print("Sent test message to", recipient)

    except Exception as exc:
        print("SMTP test failed:", exc)
        sys.exit(1)
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass


if __name__ == '__main__':
    main()
