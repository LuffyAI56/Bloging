Gmail SMTP setup for OTP delivery

This project already supports SMTP-based OTP delivery. Follow these steps to configure it to use Gmail (recommended using an App Password).

1. Create a Gmail App Password (recommended)

- Ensure your Google account has 2-Step Verification enabled.
- Go to https://myaccount.google.com/security -> "App passwords" and create a new app password for "Mail" / "Other".
- Copy the 16-character app password (no spaces).

2. Update environment variables
   Create a `.env` file in the project root (same directory as `alembic.ini`) or export these values in your environment.

Example `.env`:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-account@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM=no-reply@yourdomain.com
SEND_OTP_VIA_EMAIL=true
ENVIRONMENT=development

Notes:

- If you set `ENVIRONMENT=production`, the app will refuse to return OTP codes in API responses and will require SMTP to be configured.
- `SMTP_PASSWORD` should be an App Password (strongly preferred) rather than your account password.

3. Run the app locally
   Install deps and run with uvicorn if not already running:

```powershell
# activate your venv if needed
.\blog-env\Scripts\Activate.ps1
# run
.\blog-env\Scripts\python.exe -m uvicorn blog.main:app --reload --host 0.0.0.0 --port 8000
```

4. Test OTP request
   Use `curl` or Postman to request an OTP. With `SEND_OTP_VIA_EMAIL=true`, the API will return `{"sent": true}` if delivery succeeded.

```bash
curl -X POST http://127.0.0.1:8000/request-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'
```

Expected responses:

- In production with properly set SMTP: `{"sent": true}` and you will receive the code by email.
- In development, with `SEND_OTP_VIA_EMAIL=false` (default), the endpoint returns the OTP code in the response (convenient for local tests).

5. Troubleshooting

- If you see authentication errors from Gmail, check the `SMTP_USER` and `SMTP_PASSWORD` values and ensure App Password was used.
- Ensure your machine/network can connect to `smtp.gmail.com:587` (no firewall blocking).
- Check runtime logs for SMTP exceptions; they are propagated as 500 in the `/request-otp` handler.

6. Security reminders

- Never commit your `.env` or App Password to source control.
- Use environment-specific secrets (CI/CD or hosting provider secrets manager) in production.

If you want, I can:

- Add an SMTP health-check endpoint that attempts a STARTTLS handshake and reports status.
- Add a small script to validate SMTP settings and send a test message from the repo.
