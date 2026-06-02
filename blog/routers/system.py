"""
System routes such as SMTP health-checks and diagnostics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from email.message import EmailMessage
import smtplib
import ssl

from ..config import get_settings

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/smtp/health")
def smtp_health(send_test_to: str | None = Query(None), settings=Depends(get_settings)):
    """Checks SMTP connectivity. Optionally sends a test message when `send_test_to` is provided.

    - Returns 400 if SMTP is not configured.
    - Returns 200 with {"ok": True, "sent": true/false} on success.
    - Returns 500 with the SMTP error on failure.
    """
    if not settings.smtp_host:
        raise HTTPException(status_code=400, detail="SMTP_HOST is not configured")

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

        if send_test_to:
            msg = EmailMessage()
            msg["Subject"] = "Test email from Bloging"
            msg["From"] = settings.smtp_from
            msg["To"] = send_test_to
            msg.set_content("This is a test message sent by the Bloging SMTP health endpoint.")
            server.send_message(msg)

        return {"ok": True, "sent": bool(send_test_to)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass
