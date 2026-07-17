# Auth MVP Runbook

Quick reference for the Identity module (register / login / refresh / me) as shipped in the MVP.

## Endpoints

| Method | Path                  | Auth required | Purpose                                |
|--------|-----------------------|----------------|-----------------------------------------|
| POST   | `/api/v1/auth/register` | no           | Create a user account                   |
| POST   | `/api/v1/auth/login`    | no           | Exchange email+password for a token pair |
| POST   | `/api/v1/auth/refresh`  | no           | Rotate a refresh token for a new pair    |
| GET    | `/api/v1/auth/me`       | yes (Bearer) | Return the authenticated user            |

Access tokens are short-lived JWTs (`JWT_ACCESS_TTL_MINUTES`, default 15 min).
Refresh tokens are JWTs too, persisted server-side in `refresh_tokens` and rotated
on every use (`JWT_REFRESH_TTL_DAYS`, default 7 days). Reusing an already-rotated
refresh token is rejected.

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
| `INVALID_PASSWORD`    | 400         | Register with a password failing the password policy    |
| `INVALID_CREDENTIALS` | 401         | Login with wrong email/password                         |
| `INVALID_ACCESS_TOKEN`| 401         | `/me` with a missing, malformed, expired, or unknown-user access token |
| `INVALID_REFRESH_TOKEN` | 401       | `/refresh` with a missing, malformed, expired, revoked, or already-rotated refresh token |
| `INACTIVE_USER`       | 403         | Login/refresh/`me` for a non-ACTIVE (inactive/blocked) user |
| `INTERNAL_ERROR`      | 500         | Unhandled server error                                   |

## Running the tests

`pytest` uses a throwaway Postgres container (`docker-compose.test.yml`, port 5433,
`tmpfs` data dir) instead of the dev database on port 5432. A root-level
`conftest.py` starts it, runs migrations, and tears it down (`docker compose down -v`)
after the session — nothing written by tests persists anywhere. Requires Docker to
be running locally; no manual setup needed otherwise.

## Local smoke test

Requires a running Postgres reachable via `POSTGRES_URL` (see `.env.example`) and migrations applied (`alembic upgrade head`).

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
```

Automated coverage: `backend/modules/identity/tests/` — unit tests for use cases/domain
run against in-memory fakes; `test_auth_api.py`, `test_auth_refresh_api.py` (partially)
and `test_auth_me_api.py` (real-token cases) run against the real Postgres-backed stack.

## Known MVP limitations

- No endpoint to deactivate/block a user, so the `INACTIVE_USER` path has no way to be
  triggered through the public API today (only reachable by flipping `status` directly in the DB).
- No rate limiting or lockout on `/login` or `/refresh`.
- No password reset / email verification flow yet.
- Refresh tokens are stored as the raw JWT string (`token_hash` is not actually hashed);
  acceptable for MVP since the column isn't exposed, but should be hashed before
  handling real user data at scale.
