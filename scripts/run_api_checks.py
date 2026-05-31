from pathlib import Path
import sys

# Ensure project root is on sys.path so `import blog` works when running this script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
import os

# TestClient uses host 'testserver' by default; ensure TrustedHostMiddleware allows it
os.environ.setdefault("ALLOWED_HOSTS", "testserver,127.0.0.1,localhost")
os.environ.setdefault("ALLOWED_ORIGINS", "http://testserver")

from blog.main import app

client = TestClient(app)

endpoints = [
    ("GET", "/blog/"),
    ("GET", "/blog/categories"),
    ("GET", "/blog/tags"),
    ("GET", "/blog/trending/tags"),
]

out = {}
for method, path in endpoints:
    resp = client.request(method, path)
    try:
        data = resp.json()
    except Exception:
        data = resp.text[:200]
    out[path] = {"status_code": resp.status_code, "body_preview": data}

print(out)
