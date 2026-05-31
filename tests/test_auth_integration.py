import uuid
from fastapi.testclient import TestClient
from pathlib import Path
import os


# Ensure project root is importable when running tests directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("ALLOWED_HOSTS", "testserver,127.0.0.1,localhost")
os.environ.setdefault("ALLOWED_ORIGINS", "http://testserver")
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from blog.main import app


client = TestClient(app)


def unique_email():
    return f"test_user_{uuid.uuid4().hex[:8]}@example.com"


def test_register_login_refresh_logout_flow():
    email = unique_email()
    password = "Testpass123"

    # Register
    # Request OTP and include it during registration (dev mode returns code)
    r = client.post("/request-otp", json={"email": email})
    assert r.status_code == 200
    otp_code = r.json().get("code")

    resp = client.post("/register", json={"name": "Test User", "email": email, "password": password, "otp": otp_code})
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data

    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Login (form-encoded)
    resp = client.post("/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    data2 = resp.json()
    assert "access_token" in data2 and "refresh_token" in data2

    # Refresh token
    resp = client.post("/refresh", json={"refresh_token": data2["refresh_token"]})
    assert resp.status_code == 200
    refreshed = resp.json()
    assert refreshed.get("access_token")
    assert refreshed.get("refresh_token")

    # Logout (revoke refresh token)
    resp = client.post("/logout", json={"refresh_token": refreshed["refresh_token"]})
    assert resp.status_code == 204

    # Using the revoked refresh token should fail
    resp = client.post("/refresh", json={"refresh_token": refreshed["refresh_token"]})
    assert resp.status_code == 401 or resp.status_code == 400
