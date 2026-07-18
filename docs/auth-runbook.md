# Auth MVP Runbook

Quick reference for the Identity module (register / login / refresh / logout / me /
password reset / email verification) as shipped through Phase 8.

## Endpoints

| Method | Path                              | Auth required | Purpose                                          |
|--------|-----------------------------------|----------------|--------------------------------------------------|
| POST   | `/api/v1/auth/register`           | no           | Create a user account (sends a verification email) |
| POST   | `/api/v1/auth/login`              | no           | Exchange email+password for a token pair          |
| POST   | `/api/v1/auth/refresh`            | no           | Rotate a refresh token for a new pair             |
| POST   | `/api/v1/auth/logout`             | no           | Revoke a refresh token (single session)           |
| GET    | `/api/v1/auth/me`                 | yes (Bearer) | Return the authenticated user                     |
| POST   | `/api/v1/auth/password-reset/request` | no       | Email a password reset token, if the email exists |
| POST   | `/api/v1/auth/password-reset/confirm` | no       | Consume the token, set a new password             |
| POST   | `/api/v1/auth/verify-email/confirm`   | no       | Consume the token, mark the email verified        |

Access tokens are short-lived JWTs (`JWT_ACCESS_TTL_MINUTES`, default 15 min).
Refresh tokens are JWTs too, persisted server-side in `refresh_tokens` and rotated
on every use (`JWT_REFRESH_TTL_DAYS`, default 7 days). Reusing an already-rotated
refresh token is rejected. `logout` and a successful `password-reset/confirm` both
revoke via the same server-side row — logout revokes just the one token passed in,
a password reset revokes **every** refresh token the user holds (forces re-login
on all other sessions/devices).

`email_verified` is tracked on the user (`GET /me`) but does **not** gate login —
an unverified user can authenticate normally. This is a deliberate scope boundary,
not an oversight.

## Error format

Every error response — validation, business, or unexpected — has the same shape:

```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "Invalid credentials",
  "timestamp": "2026-07-17T16:46:53Z"
}
```

`code` values used by the auth endpoints:

| code                  | HTTP status | Where it comes from                                   |
|-----------------------|-------------|--------------------------------------------------------|
| `VALIDATION_ERROR`    | 422         | Malformed request body (missing/invalid fields)         |
| `USER_ALREADY_EXISTS` | 409         | Register with an email already in use                   |
| `INVALID_PASSWORD`    | 400         | Password fails the password policy (register or reset confirm) |
| `INVALID_CREDENTIALS` | 401         | Login with wrong email/password                         |
| `INVALID_ACCESS_TOKEN`| 401         | `/me` with a missing, malformed, expired, or unknown-user access token |
| `INVALID_REFRESH_TOKEN` | 401       | `/refresh` with a missing, malformed, expired, revoked, or already-rotated refresh token |
| `BAD_REQUEST`         | 400         | `password-reset/confirm` or `verify-email/confirm` with an invalid, expired, already-used token, or a token whose user no longer exists |
| `INACTIVE_USER`       | 403         | Login/refresh/`me` for a non-ACTIVE (inactive/blocked) user |
| `INTERNAL_ERROR`      | 500         | Unhandled server error                                   |

`password-reset/request` and `logout` never return an error — both are designed to
be `200` unconditionally (the former to avoid revealing whether an email is
registered; the latter because revoking an already-invalid token is a no-op, not
a failure).

## Running the tests

`pytest` uses a throwaway Postgres container (`docker-compose.test.yml`, port 5433,
`tmpfs` data dir) instead of the dev database on port 5432. A root-level
`conftest.py` starts it, runs migrations, and tears it down (`docker compose down -v`)
after the session — nothing written by tests persists anywhere. Requires Docker to
be running locally; no manual setup needed otherwise.

Real-Postgres API tests that need to observe a one-time email token (password
reset, email verification) override just the `get_email_sender` FastAPI dependency
with a shared `FakeEmailSender` per test — every other dependency (repositories,
use cases) still resolves against the real test Postgres via the `client` fixture.
This keeps persistence real while making the raw token assertable, without
introducing a second, fakes-only test client just for these two flows.

## Local smoke test

Requires a running Postgres reachable via `POSTGRES_URL` (see `.env.example`),
migrations applied (`alembic upgrade head`), and — for the password-reset/
email-verification steps — Mailhog running (`docker compose up -d mailhog`,
`EMAIL_PROVIDER=smtp`) with its web UI at `http://localhost:8025`.

```bash
curl -s localhost:8000/api/v1/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"demo@example.com","password":"StrongPass123"}'

curl -s localhost:8000/api/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"demo@example.com","password":"StrongPass123"}'

curl -s localhost:8000/api/v1/auth/me \
  -H "authorization: Bearer <access_token from login>"

curl -s localhost:8000/api/v1/auth/refresh \
  -H 'content-type: application/json' \
  -d '{"refresh_token":"<refresh_token from login>"}'

curl -s localhost:8000/api/v1/auth/logout \
  -H 'content-type: application/json' \
  -d '{"refresh_token":"<refresh_token to revoke>"}'
```

Password reset / email verification — the raw token only ever exists in the
email body, so fetch it from Mailhog's HTTP API (`GET /api/v2/messages`) rather
than the response body:

```bash
curl -s -X POST localhost:8000/api/v1/auth/password-reset/request \
  -H 'content-type: application/json' \
  -d '{"email":"demo@example.com"}'

# fetch the raw token from http://localhost:8025/api/v2/messages, then:
curl -s -X POST localhost:8000/api/v1/auth/password-reset/confirm \
  -H 'content-type: application/json' \
  -d '{"token":"<raw token from the email body>","new_password":"NewStrongPass456"}'

# registration already sent a verification email — fetch its token the same way:
curl -s -X POST localhost:8000/api/v1/auth/verify-email/confirm \
  -H 'content-type: application/json' \
  -d '{"token":"<raw token from the email body>"}'
```

Automated coverage: `backend/modules/identity/tests/` — unit tests for use cases/domain
run against in-memory fakes; `test_auth_api.py`, `test_auth_refresh_api.py` (partially),
`test_auth_me_api.py` (real-token cases), `test_logout_api.py`, `test_password_reset_api.py`,
and `test_email_verification_api.py` run against the real Postgres-backed stack.

## Known MVP limitations

- No endpoint to deactivate/block a user, so the `INACTIVE_USER` path has no way to be
  triggered through the public API today (only reachable by flipping `status` directly in the DB).
- No rate limiting or lockout on `/login`, `/refresh`, or `/password-reset/request`
  — the last one matters most, since it's the one unauthenticated endpoint that
  triggers a real email send per call.
- `logout` only revokes the one refresh token passed in — there's no "list my
  active sessions" or "log out everywhere" self-service endpoint (a password
  reset does revoke everywhere, but only as a side effect of changing the
  password, not as a standalone action).
- Refresh tokens are stored as the raw JWT string (`token_hash` is not actually hashed);
  acceptable for MVP since the column isn't exposed, but should be hashed before
  handling real user data at scale.
- The failed-email retry mechanism (background timer, up to 10 attempts) only
  has strategies wired for `PASSWORD_RESET` and `EMAIL_VERIFICATION` — any future
  email purpose needs its own `EmailRetryStrategy` registered, or it fails
  permanently after one attempt with a "no retry strategy registered" error.
