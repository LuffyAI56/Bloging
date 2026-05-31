import uuid
from types import SimpleNamespace
from fastapi.testclient import TestClient
from pathlib import Path
import os

# Ensure project root is importable when running tests directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("ALLOWED_HOSTS", "testserver,127.0.0.1,localhost")
os.environ.setdefault("ALLOWED_ORIGINS", "http://testserver")
import sys
sys.path.insert(0, str(PROJECT_ROOT))

import blog.routers.authentication as auth_router
from blog.main import app

client = TestClient(app)


def unique_email():
    return f"otp_user_{uuid.uuid4().hex[:8]}@example.com"


def test_register_requires_otp_if_not_verified():
    email = unique_email()
    password = "Testpass123"

    # Attempting to register without requesting/verifying OTP should fail
    resp = client.post("/register", json={"name": "User", "email": email, "password": password})
    assert resp.status_code == 400


def test_request_otp_rate_limits_by_email():
    email = unique_email()

    for _ in range(auth_router.OTP_EMAIL_LIMIT):
        resp = client.post("/request-otp", json={"email": email})
        assert resp.status_code == 200

    resp = client.post("/request-otp", json={"email": email})
    assert resp.status_code == 429
    assert "OTP request limit exceeded" in resp.json().get("detail", "")


def test_request_otp_via_smtp_and_register(monkeypatch):
    email = unique_email()
    password = "Testpass123"

    # Patch settings to enable SMTP sending in the authentication router
    import blog.routers.authentication as auth_router

    monkeypatch.setattr(
        auth_router,
        "get_settings",
        lambda: SimpleNamespace(
            send_otp_via_email=True,
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user=None,
            smtp_password=None,
            smtp_from="no-reply@example.com",
        ),
    )

    sent = {}

    def fake_send(recipient, code):
        sent["recipient"] = recipient
        sent["code"] = code

    monkeypatch.setattr(auth_router, "send_otp_email", fake_send)

    # Request OTP - should return sent=True and our fake_send should have captured the code
    r = client.post("/request-otp", json={"email": email})
    assert r.status_code == 200
    assert r.json().get("sent") is True
    assert sent.get("code")
    assert sent.get("recipient") == email

    # Verify OTP using the captured code
    v = client.post("/verify-otp", json={"email": email, "code": sent.get("code")})
    assert v.status_code == 200
    assert v.json().get("verified") is True

    # Now register without passing OTP (two-step flow)
    resp = client.post("/register", json={"name": "User", "email": email, "password": password})
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data
