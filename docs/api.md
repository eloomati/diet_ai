# Diet AI - API Contract

## Overview

This document defines the REST API contract for the Diet AI application.
It's a hand-written, narrative companion to the machine-generated
OpenAPI/Swagger schema — see **Machine-readable schema** below for where
that lives and how the two relate.

The API provides functionality for:

- user registration and authentication,
- password reset and email verification,
- nutrition profile management, including a weekly obligations schedule,
- AI conversations,
- conversation history, archiving, and deletion,
- diet plan generation, AI-suggested + user-editable meal scheduling,
- diet plan CSV export (archived for later re-download) and date-range filtering of plan history,
- dietitian applications and (once approved) dietitian profile management, including up to 3 photos,
- admin user management and dietitian-application review (ADMIN/SUPER_ADMIN-only).

Base URL:

```
/api/v1
```

Authentication:

Protected endpoints require JWT authentication:

```
Authorization: Bearer {access_token}
```

## Machine-readable schema

`docs/openapi.json` is the full OpenAPI 3.1 schema, generated directly
from the running FastAPI app (`app.openapi()`) — not hand-maintained, so
it can't drift from the actual request/response shapes the way a
hand-written doc can. Regenerate it after any endpoint change:

```bash
PYTHONPATH=. python scripts/export_openapi.py
```

The same schema is also always available live at `/openapi.json`
(and rendered interactively at `/docs`) whenever the app is running — the
committed file is a point-in-time snapshot for browsing/diffing without
starting the server, or importing into external tools (Postman, client
generators, etc.). This document (`api.md`) stays the place for prose:
*why* an endpoint behaves the way it does (e.g. the not-found-vs-not-yours
ambiguity, the generic password-reset response) — detail the schema alone
can't carry.

---

# Authentication API

Module:

```
Identity
```

Database:

```
PostgreSQL
```

---

## POST /auth/register

Creates a new user account.

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPass123",
  "captcha_token": "<token from the CAPTCHA widget>"
}
```

Password: 8-128 characters, must satisfy `PasswordPolicy` (see domain-model.md).

`captcha_token`: required, verified server-side against the configured
provider (`CAPTCHA_PROVIDER` — `mock` always accepts in dev/tests,
`turnstile` calls Cloudflare's `siteverify` for real) before anything else
happens — same "fail before real work" shape as the diet-plan
profile-required check.

### Response

Status:

```
201 Created
```

Body:

```json
{
  "user_id": "uuid",
  "email": "user@example.com"
}
```

### Errors

400 Bad Request — `INVALID_PASSWORD` (fails password policy)

400 Bad Request — `BAD_REQUEST` (CAPTCHA verification failed)

422 Unprocessable Entity — `VALIDATION_ERROR` (malformed email / missing fields, including a missing `captcha_token`)

409 Conflict — `USER_ALREADY_EXISTS`

---

## POST /auth/login

Authenticates a user and issues a token pair.

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPass123"
}
```

### Response

Status:

```
200 OK
```

Body:

```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "token_type": "bearer"
}
```

`access_token` TTL: `JWT_ACCESS_TTL_MINUTES` (default 15 min).
`refresh_token` TTL: `JWT_REFRESH_TTL_DAYS` (default 7 days).

### Errors

401 Unauthorized — `INVALID_CREDENTIALS`

403 Forbidden — `INACTIVE_USER`

---

## POST /auth/refresh

Rotates a refresh token: the token sent in the request is invalidated and a new
access/refresh pair is issued. Reusing an already-rotated (or expired/unknown)
refresh token is rejected.

### Request

```json
{
  "refresh_token": "refresh-token"
}
```

### Response

```json
{
  "access_token": "new-jwt-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer"
}
```

### Errors

401 Unauthorized — `INVALID_REFRESH_TOKEN`

403 Forbidden — `INACTIVE_USER`

---

## POST /auth/logout

Revokes a refresh token. Idempotent — an unknown, garbage, or already
revoked/expired token still returns `200` (the caller only cares that the
token can no longer be used, which already holds). Only revokes the one
session's refresh token, not every session the user is logged into — see
`revoke_all_for_user` in `docs/architecture.md` for the "revoke everywhere"
case used by password reset.

### Request

```json
{
  "refresh_token": "refresh-token"
}
```

### Response

Status:

```
200 OK
```

Body:

```json
{
  "message": "Logged out successfully."
}
```

### Errors

None — always `200`, even for an unknown/garbage token.

---

## GET /auth/me

Returns the authenticated user.

Authentication:

Required — `Authorization: Bearer {access_token}`.

### Response

Status:

```
200 OK
```

Body:

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "status": "ACTIVE",
  "role": "USER",
  "email_verified": false
}
```

`role`: one of `USER`, `DIET_USER`, `ADMIN`, `SUPER_ADMIN` — every user
is `USER` until either a `SUPER_ADMIN` promotes them (see
`PATCH /admin/users/{user_id}/role` below) or a future dietitian-
application approval flow promotes them to `DIET_USER` (Phase 12).

### Errors

401 Unauthorized — `INVALID_ACCESS_TOKEN` (missing/malformed/expired token, or token references a deleted user)

403 Forbidden — `INACTIVE_USER`

---

## PATCH /admin/users/{user_id}/role

Changes another user's role. `SUPER_ADMIN`-only — this is the only way
any user ever gains `ADMIN`/`SUPER_ADMIN`/`DIET_USER`; there is no
self-escalation path anywhere in the API. A `SUPER_ADMIN` also cannot
change their *own* role through this endpoint (400) — otherwise the
only `SUPER_ADMIN` in the system could accidentally demote or lock
themselves out with a single request.

Authentication:

Required — `Authorization: Bearer {access_token}`, and the caller's own
role must be `SUPER_ADMIN`.

### Request

```json
{
  "new_role": "DIET_USER"
}
```

`new_role`: one of `USER`, `DIET_USER`, `ADMIN`, `SUPER_ADMIN`.

### Response

Status:

```
200 OK
```

Body:

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "DIET_USER"
}
```

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not SUPER_ADMIN
400 Bad Request code=BAD_REQUEST — user_id is the caller's own id
404 Not Found code=NOT_FOUND — user_id doesn't exist
422 Unprocessable Entity code=VALIDATION_ERROR — new_role isn't one of the 4 valid values
```

---

## POST /auth/password-reset/request

Issues a password reset token (30 min TTL) and emails it to the given
address, if an account with that address exists. Always returns the same
generic `200` regardless — this endpoint never reveals whether the email
is registered.

### Request

```json
{
  "email": "user@example.com",
  "captcha_token": "<token from the CAPTCHA widget>"
}
```

`captcha_token`: required, checked before the don't-leak-existence logic
below — a failed CAPTCHA rejects outright and reveals nothing about the
email either (same provider/verification as `POST /auth/register`).

### Response

Status:

```
200 OK
```

Body:

```json
{
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

### Errors

400 Bad Request — `BAD_REQUEST` (CAPTCHA verification failed)

422 Unprocessable Entity — `VALIDATION_ERROR` (missing `captcha_token`)

Otherwise always `200`, whether or not the email exists.

---

## POST /auth/password-reset/confirm

Consumes a password reset token, sets the new password, and — as a
side effect — revokes every refresh token the user currently holds (forcing
re-login on all other sessions/devices, standard practice after a
credential reset).

### Request

```json
{
  "token": "raw-token-from-email",
  "new_password": "NewStrongPass456"
}
```

`new_password`: 8-128 characters, must satisfy `PasswordPolicy` (same rule
as registration).

### Response

Status:

```
200 OK
```

Body:

```json
{
  "message": "Password has been reset successfully."
}
```

### Errors

400 Bad Request — `BAD_REQUEST` (token invalid, expired, already used, or its user no longer exists)

400 Bad Request — `INVALID_PASSWORD` (`new_password` fails `PasswordPolicy`)

422 Unprocessable Entity — `VALIDATION_ERROR` (`new_password` shorter than 8 chars)

---

## POST /auth/verify-email/confirm

Consumes the verification token sent at registration and marks the user's
email as verified (`GET /auth/me`'s `email_verified` flips to `true`).
**Not** a login gate — an unverified user can still authenticate normally
(see auth-runbook.md); this only tracks the flag.

### Request

```json
{
  "token": "raw-token-from-email"
}
```

### Response

Status:

```
200 OK
```

Body:

```json
{
  "message": "Email verified successfully."
}
```

### Errors

400 Bad Request — `BAD_REQUEST` (token invalid, expired, already used, or its user no longer exists)

---

# Nutrition Profile API

Module:

```
Nutrition
```

Database:

```
MongoDB
```

---

All endpoints below require `Authorization: Bearer {access_token}`.

Enums:

```
activity_level: LOW | MODERATE | HIGH | VERY_HIGH
goal:           WEIGHT_LOSS | MUSCLE_GAIN | MAINTENANCE | PERFORMANCE
diet_type:      STANDARD | VEGETARIAN | VEGAN | KETO | PALEO | GLUTEN_FREE
```

One profile per user — `POST` on a user who already has one returns `409`.

`weekly_obligations` (Phase 9): a list of recurring weekly time blocks
(work, training, ...) the caller wants diet-plan generation to schedule
meals around (see `POST /diet-plans/generate` below). Optional — omit or
send `[]` for none.

```
day_of_week: MON | TUE | WED | THU | FRI | SAT | SUN
start_time / end_time: "HH:MM:SS" (end must be after start)
label: free text, 1-100 chars
```

## GET /profile

Returns the authenticated user's nutrition profile.

### Response

Status:

```
200 OK
```

Body:

```json
{
  "profile_id": "uuid",
  "user_id": "uuid",
  "age": 29,
  "height_cm": 187,
  "weight_kg": 80.0,
  "activity_level": "HIGH",
  "goal": "MUSCLE_GAIN",
  "diet_type": "VEGETARIAN",
  "weekly_obligations": [
    {
      "day_of_week": "MON",
      "start_time": "09:00",
      "end_time": "17:00",
      "label": "Work"
    }
  ],
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

Errors:

```
404 Not Found  code=NOT_FOUND        — user has no profile yet
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/invalid token
```

---

## POST /profile

Creates the authenticated user's nutrition profile.

### Request

```json
{
  "age": 29,
  "height_cm": 187,
  "weight_kg": 80,
  "activity_level": "HIGH",
  "goal": "MUSCLE_GAIN",
  "diet_type": "VEGETARIAN",
  "weekly_obligations": [
    {
      "day_of_week": "MON",
      "start_time": "09:00:00",
      "end_time": "17:00:00",
      "label": "Work"
    }
  ]
}
```

Validation: `age` 1-120, `height_cm` 50-250, `weight_kg` 20-400 (422
`VALIDATION_ERROR` otherwise); each `weekly_obligations` entry's `end_time`
must be after `start_time` (400 `BAD_REQUEST` otherwise — not a simple
field-range check, so it's caught at the domain layer, not by schema
validation).

### Response

Status:

```
201 Created
```

Body: same shape as `GET /profile`.

Errors:

```
409 Conflict code=CONFLICT — profile already exists for this user
400 Bad Request code=BAD_REQUEST — a weekly_obligations entry has end_time <= start_time
```

---

## PUT /profile

Partially updates the authenticated user's nutrition profile — only the
provided fields change, the rest are kept as-is. `weekly_obligations`
follows the same rule: omit the field entirely to leave the existing
schedule untouched, or send `[]` to clear it.

### Request

```json
{
  "weight_kg": 82,
  "activity_level": "VERY_HIGH"
}
```

### Response

Status:

```
200 OK
```

Body: same shape as `GET /profile`, with updated fields.

Errors:

```
404 Not Found code=NOT_FOUND — user has no profile to update yet
400 Bad Request code=BAD_REQUEST — a weekly_obligations entry has end_time <= start_time
```

---

# Conversation API

Module:

```
Conversation
```

Database:

```
MongoDB
```

---

All endpoints below require `Authorization: Bearer {access_token}`.

## POST /conversations

Creates a new conversation. `categories` is a list — a conversation can be
steered by more than one category at once (e.g. `["DIET", "RUNNING"]` for a
race-prep nutrition chat); at least one is required.

### Request

```json
{
  "title": "High protein breakfasts",
  "categories": ["BREAKFAST", "DIET"]
}
```

### Response

Status:

```
201 Created
```

Body:

```json
{
  "conversation_id": "uuid",
  "title": "High protein breakfasts",
  "categories": ["BREAKFAST", "DIET"],
  "status": "ACTIVE"
}
```

### Errors

401 Unauthorized — missing/invalid token (see auth-runbook.md)

422 Unprocessable Entity — `VALIDATION_ERROR` (invalid category value, empty
`categories` list, empty `title`)

---

## GET /conversations

Returns conversation summaries belonging to the authenticated user (no messages — use `GET /conversations/{id}` for those).

### Response

Status:

```
200 OK
```

Body:

```json
[
  {
    "conversation_id": "uuid",
    "title": "High protein breakfasts",
    "categories": ["BREAKFAST", "DIET"],
    "status": "ACTIVE",
    "updated_at": "2026-01-01T12:00:00Z"
  }
]
```

---

## GET /conversations/{conversation_id}

Returns a single conversation with its full message history.

### Response

Status:

```
200 OK
```

Body:

```json
{
  "conversation_id": "uuid",
  "title": "High protein breakfasts",
  "categories": ["BREAKFAST", "DIET"],
  "status": "ACTIVE",
  "messages": [
    {
      "id": "uuid",
      "role": "USER",
      "content": "Create breakfast ideas",
      "created_at": "2026-01-01T10:01:00Z"
    },
    {
      "id": "uuid",
      "role": "ASSISTANT",
      "content": "Here are ideas...",
      "created_at": "2026-01-01T10:01:05Z"
    }
  ]
}
```

### Errors

404 Not Found — `NOT_FOUND` (conversation doesn't exist, or belongs to another user — both look identical, to avoid leaking existence)

---

## POST /conversations/{conversation_id}/messages

Appends a user message, generates an AI response (via whichever provider `AI_PROVIDER` selects — see auth-runbook.md-style config in `.env.example`), appends the response, and returns both.

### Request

```json
{
  "content": "I run 5 times a week. Create high protein breakfasts for 7 days."
}
```

### Response

Status:

```
201 Created
```

Body:

```json
{
  "conversation_id": "uuid",
  "user_message_id": "uuid",
  "assistant_message_id": "uuid",
  "assistant_content": "Here is your weekly breakfast plan..."
}
```

### Errors

404 Not Found — `NOT_FOUND` (same not-found-vs-not-yours ambiguity as above)

409 Conflict — `CONFLICT` (conversation is archived — see below)

---

## POST /conversations/{conversation_id}/archive

Archives a conversation. An archived conversation is still readable
(`GET /conversations/{id}`) but rejects new messages.

### Response

Status:

```
200 OK
```

Body: same shape as `GET /conversations/{conversation_id}`, with
`"status": "ARCHIVED"`.

### Errors

404 Not Found — `NOT_FOUND` (same not-found-vs-not-yours ambiguity as above)

---

## DELETE /conversations/{conversation_id}

Permanently deletes a conversation and its full message history. Not
reversible — there is no undo/restore endpoint.

### Response

Status:

```
204 No Content
```

### Errors

404 Not Found — `NOT_FOUND` (same not-found-vs-not-yours ambiguity as above)

---

# Diet Plan API

Module:

```
Nutrition
```

All endpoints below require `Authorization: Bearer {access_token}`. Only
`POST /diet-plans/generate` requires a nutrition profile to already exist
for the caller (`POST /profile` — see Nutrition Profile API above) — the
other six endpoints (list, get, reschedule, and the three export
endpoints) only check plan/export ownership, never the profile. `goal`
and `diet_type` are **not** request fields on generation — they're read
from the caller's existing `NutritionProfile`, the same way chat
responses are personalized from it.

---

## POST /diet-plans/generate

Generates a personalized, structured multi-day diet plan using AI, seeded
from the caller's nutrition profile plus optional free-text requirements.

### Request

```json
{
  "duration_days": 3,
  "requirements": ["high protein breakfasts"]
}
```

`duration_days`: 1-14 (422 `VALIDATION_ERROR` outside that range).
`requirements`: optional list of free-text hints — omit or send `null`/`[]`
for none.

### Response

Status:

```
201 Created
```

Body:

```json
{
  "plan_id": "uuid",
  "user_id": "uuid",
  "goal": "MUSCLE_GAIN",
  "diet_type": "VEGETARIAN",
  "duration_days": 3,
  "requirements": ["high protein breakfasts"],
  "days": [
    {
      "day_number": 1,
      "meals": [
        {
          "name": "Protein oatmeal",
          "calories": 600,
          "protein": 45,
          "carbohydrates": 70,
          "fat": 15,
          "time": "08:00"
        }
      ]
    }
  ],
  "created_at": "2026-01-01T10:00:00.482391+00:00",
  "updated_at": "2026-01-01T10:00:00.482391+00:00"
}
```

`created_at`/`updated_at` are plain `datetime.isoformat()` output —
microseconds and a `+00:00` offset, **not** `Z`-normalized like the error
envelope's `timestamp` field below.

`time` (Phase 9): AI-suggested time of day for the meal, `"HH:MM"` or
`null` if the model didn't provide one (never required — see
architecture.md for why). If the caller's profile has
`weekly_obligations`, a suggested time colliding with one is nudged to the
nearest free slot after generation — see architecture.md's conflict-clamping
note. `updated_at` starts equal to `created_at` and only moves once a meal
is rescheduled (see `PATCH .../meals` below).

Errors:

```
404 Not Found code=NOT_FOUND — caller has no nutrition profile yet (create
                one via POST /profile first)
500 Internal Server Error code=INTERNAL_ERROR — the AI provider returned a
                malformed/unparseable plan; retried once internally
                (Ollama only) before giving up — no silent fallback to a
                broken plan. Rare with Claude (native structured output);
                more likely with the small local Ollama model, especially
                when `requirements` is non-empty — retrying the request
                usually succeeds.
```

---

## PATCH /diet-plans/{diet_plan_id}/meals

Reschedules a single meal's time within an already-generated plan. The
only mutation a plan ever undergoes after generation — everything else
about it (macros, meal identity, day count) is immutable.

### Request

```json
{
  "day_number": 1,
  "meal_name": "Protein oatmeal",
  "new_time": "07:30:00"
}
```

### Response

Status:

```
200 OK
```

Body: same shape as `POST /diet-plans/generate`, with only the targeted
meal's `time` changed and `updated_at` bumped.

Errors:

```
404 Not Found code=NOT_FOUND — plan doesn't exist, or belongs to another user
400 Bad Request code=BAD_REQUEST — day_number or meal_name doesn't exist
                within this plan (the plan itself is fine, so this is 400,
                not 404 — see architecture.md)
422 Unprocessable Entity code=VALIDATION_ERROR — day_number < 1, or
                meal_name is empty — request-shape validation, checked
                before the day/meal lookup above ever runs
```

---

## GET /diet-plans

Lists the caller's own generated diet plans, newest first (summary only —
no `days`/`meals`).

### Query parameters

```
from: ISO date ("2026-01-01") — only plans created on/after this date
to:   ISO date — only plans created on/before this date (inclusive of the
      whole day)
```

Both optional; omit either or both to not filter on that bound. Purely a
display filter — nothing is ever deleted based on this range.

### Response

Status:

```
200 OK
```

Body:

```json
[
  {
    "plan_id": "uuid",
    "goal": "MUSCLE_GAIN",
    "diet_type": "VEGETARIAN",
    "duration_days": 3,
    "created_at": "2026-01-01T10:00:00.482391+00:00"
  }
]
```

Errors:

```
400 Bad Request code=BAD_REQUEST — from is after to
422 Unprocessable Entity code=VALIDATION_ERROR — from/to isn't a valid
                ISO date (e.g. "from=not-a-date")
```

---

## POST /diet-plans/{diet_plan_id}/export

Builds a CSV export of the plan (day, date, time, meal, macros) and
archives it on the configured SFTP server — this does **not** return the
file itself, only its metadata, so it can be re-downloaded later without
regenerating it (see `GET .../exports/{export_id}/download`). A plan can
be exported more than once (e.g. after rescheduling a meal); each export
is its own separate archived file, never an overwrite.

### Response

Status:

```
201 Created
```

Body:

```json
{
  "export_id": "uuid",
  "diet_plan_id": "uuid",
  "filename": "3fa8...-a1b2c3d4.csv",
  "created_at": "2026-01-01T10:05:00.482391+00:00"
}
```

Errors:

```
404 Not Found code=NOT_FOUND — plan doesn't exist, or belongs to another user
```

---

## GET /diet-plans/{diet_plan_id}/exports

Lists previous exports of this plan, newest first.

### Response

Status:

```
200 OK
```

Body: array of the same shape as `POST .../export`'s response.

Errors:

```
404 Not Found code=NOT_FOUND — plan doesn't exist, or belongs to another user
```

---

## GET /diet-plans/{diet_plan_id}/exports/{export_id}/download

Streams a previously archived export back as a CSV file
(`Content-Type: text/csv`, `Content-Disposition: attachment`). The backend
fetches the file from the SFTP server server-side — SFTP has no
presigned-URL equivalent, so this always proxies through the API rather
than redirecting.

### Response

Status:

```
200 OK
```

Errors:

```
404 Not Found code=NOT_FOUND — export doesn't exist, doesn't belong to the
                caller, or doesn't belong to the diet_plan_id in the URL
```

---

## GET /diet-plans/{diet_plan_id}

Returns one full diet plan (with `days`/`meals`) — same body shape as the
`POST /diet-plans/generate` response.

### Response

Status:

```
200 OK
```

Errors:

```
404 Not Found code=NOT_FOUND — plan doesn't exist, or belongs to another
                user (not distinguished, so existence isn't leaked)
```

---

# Dietitian API

Module:

```
Dietitian
```

Database:

```
PostgreSQL
```

All endpoints below require `Authorization: Bearer {access_token}`. The
application endpoints (`POST`/`GET .../applications*`) are open to any
authenticated `USER`. The profile endpoints (`.../profile*`) additionally
require the caller's role to already be `DIET_USER` — there is currently
no API path that grants `DIET_USER` or creates the `DietitianProfile` row
(that's the admin-approval flow, not yet built); until it exists, both
are set directly against Postgres out of band.

---

## POST /dietitian/applications

Submits a dietitian application. One application per user, ever — a
second submission is rejected regardless of the first one's status (no
reapply-after-rejection flow in this MVP scope).

### Request

```json
{
  "experience": "5 years as a clinical dietitian",
  "diplomas": ["MSc Dietetics"],
  "description": "I specialize in weight management and sports nutrition."
}
```

`diplomas` may be an empty list.

### Response

Status:

```
201 Created
```

Body:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "experience": "5 years as a clinical dietitian",
  "diplomas": ["MSc Dietetics"],
  "description": "I specialize in weight management and sports nutrition.",
  "status": "PENDING",
  "created_at": "2026-07-19T12:00:00+00:00"
}
```

`status` is one of `PENDING`, `APPROVED`, `REJECTED` — always `PENDING`
on submission.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
409 Conflict code=CONFLICT — an application already exists for this user
422 Unprocessable Entity code=VALIDATION_ERROR — experience/description blank
```

---

## GET /dietitian/applications/me

Returns the caller's own application, whatever its status — lets the
frontend show "pending"/"approved"/"rejected" instead of the apply
button once one exists.

### Response

Status:

```
200 OK
```

Body: same shape as `POST /dietitian/applications`'s response.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
404 Not Found code=NOT_FOUND — no application submitted yet
```

---

## GET /dietitian/profile/me

Returns the caller's own dietitian profile.

Authentication:

Required — caller's role must be `DIET_USER`.

### Response

Status:

```
200 OK
```

Body:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "experience": "5 years as a clinical dietitian",
  "diplomas": ["MSc Dietetics"],
  "description": "I specialize in weight management and sports nutrition.",
  "photos": ["/static/dietitian-photos/<uuid>.jpg"],
  "created_at": "2026-07-19T12:00:00+00:00"
}
```

`photos` holds up to 3 entries — each a root-absolute path served by a
static file mount, not under `/api/v1` (see `POST .../photos` below).

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not DIET_USER
404 Not Found code=NOT_FOUND — no profile exists for this user
```

---

## PUT /dietitian/profile

Partial update — only the given fields change (same convention as
`PUT /profile`). At least one field should be given, but none are
individually required.

Authentication:

Required — caller's role must be `DIET_USER`.

### Request

```json
{
  "description": "Updated description."
}
```

`experience`, `diplomas`, `description` — all optional.

### Response

Status:

```
200 OK
```

Body: same shape as `GET /dietitian/profile/me`.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not DIET_USER
404 Not Found code=NOT_FOUND — no profile exists for this user
400 Bad Request code=BAD_REQUEST — experience/description blanked out
```

---

## POST /dietitian/profile/photos

Uploads one photo, appending it to the profile's `photos` list — up to
3 total. `multipart/form-data`, field name `file`. Accepts
`image/jpeg`, `image/png`, `image/webp`, max 5 MB. Stored on local disk
(MVP decision, not object storage) under a server-generated filename —
the client's own filename is never trusted beyond its extension, which
also rules out path traversal by construction.

Authentication:

Required — caller's role must be `DIET_USER`.

### Response

Status:

```
201 Created
```

Body: same shape as `GET /dietitian/profile/me`, with the new photo
appended to `photos`.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not DIET_USER
404 Not Found code=NOT_FOUND — no profile exists for this user
400 Bad Request code=BAD_REQUEST — unsupported content-type, file over 5 MB,
                                     or the profile already has 3 photos
```

---

## DELETE /dietitian/profile/photos/{index}

Removes the photo at `index` (0-based, matching the `photos` array
order returned by `GET .../me`) from the profile. The file itself is
left on disk — this endpoint only detaches it from the profile record.

Authentication:

Required — caller's role must be `DIET_USER`.

### Response

Status:

```
200 OK
```

Body: same shape as `GET /dietitian/profile/me`, with the photo removed
from `photos`.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not DIET_USER
404 Not Found code=NOT_FOUND — no profile exists for this user
400 Bad Request code=BAD_REQUEST — index out of range
```

---

# Admin API

Module:

```
Admin
```

Database:

```
none — this module has no persistence of its own; see docs/architecture.md
```

All endpoints below require `Authorization: Bearer {access_token}` and
the caller's role to be `ADMIN` or `SUPER_ADMIN`. Changing a user's role
directly (as opposed to via dietitian-application approval, below) is a
separate, `SUPER_ADMIN`-only endpoint — see
`PATCH /admin/users/{user_id}/role` under the Authentication API above.

---

## GET /admin/users

Lists every user account.

### Response

Status:

```
200 OK
```

Body:

```json
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "status": "ACTIVE",
    "role": "USER",
    "email_verified": false,
    "created_at": "2026-07-19T12:00:00+00:00"
  }
]
```

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not ADMIN/SUPER_ADMIN
```

---

## POST /admin/users/{user_id}/activate

Sets the user's status to `ACTIVE`.

### Response

Status:

```
200 OK
```

Body: same shape as one entry of `GET /admin/users`.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not ADMIN/SUPER_ADMIN
404 Not Found code=NOT_FOUND — user_id doesn't exist
```

---

## POST /admin/users/{user_id}/ban

Sets the user's status to `BLOCKED` — they can no longer authenticate.

### Response

Status:

```
200 OK
```

Body: same shape as one entry of `GET /admin/users`.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not ADMIN/SUPER_ADMIN
404 Not Found code=NOT_FOUND — user_id doesn't exist
```

---

## DELETE /admin/users/{user_id}

Permanently deletes the user and all of their data — Postgres rows
(refresh/reset/verification tokens, dietitian application/profile, via
`ON DELETE CASCADE`) and Mongo documents (conversations, nutrition
profile, diet plans, diet plan exports, deleted explicitly since
Postgres cascades can't reach Mongo). `email_logs` rows are
deliberately left behind — they have no foreign key to the user by
design. Cannot be undone.

An admin cannot delete their own account through this endpoint.

### Response

Status:

```
204 No Content
```

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not ADMIN/SUPER_ADMIN
400 Bad Request code=BAD_REQUEST — user_id is the caller's own id
404 Not Found code=NOT_FOUND — user_id doesn't exist
```

---

## GET /admin/dietitian-applications

Lists dietitian applications, optionally filtered by status.

### Query parameters

```
status   optional, one of PENDING | APPROVED | REJECTED
```

### Response

Status:

```
200 OK
```

Body: an array in the same shape as `POST /dietitian/applications`'s
response (see the Dietitian API above).

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not ADMIN/SUPER_ADMIN
```

---

## POST /admin/dietitian-applications/{application_id}/approve

Approves the application: sets its status to `APPROVED`, promotes the
applicant's role to `DIET_USER`, and creates their `DietitianProfile`
from the application's own experience/diplomas/description (unless one
already exists, which is not expected in normal operation).

### Response

Status:

```
200 OK
```

Body: same shape as `GET /admin/dietitian-applications`'s entries.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not ADMIN/SUPER_ADMIN
404 Not Found code=NOT_FOUND — application_id doesn't exist
409 Conflict code=CONFLICT — application was already approved/rejected
```

---

## POST /admin/dietitian-applications/{application_id}/reject

Rejects the application: sets its status to `REJECTED`. Does not change
the applicant's role.

### Response

Status:

```
200 OK
```

Body: same shape as `GET /admin/dietitian-applications`'s entries.

### Errors

```
401 Unauthorized code=INVALID_ACCESS_TOKEN — missing/malformed/expired token
403 Forbidden code=FORBIDDEN — caller's role is not ADMIN/SUPER_ADMIN
404 Not Found code=NOT_FOUND — application_id doesn't exist
409 Conflict code=CONFLICT — application was already approved/rejected
```

---

# Conversation Categories

Available categories (closed enum — steers/guides the conversation, fed into the
AI prompt; adding a new one is a code change, not a runtime CRUD operation):

```
GENERAL

DIET

BREAKFAST

FITNESS

RUNNING

GYM

HEALTH

SUPPLEMENTS
```

Categories influence:

- prompt generation,
- AI context,
- future business rules.

---

# Common Error Format

All API errors use the same structure — including request validation errors
(422) and unhandled exceptions (500), not just business errors.

```json
{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "timestamp": "2026-01-01T10:00:00Z"
}
```

Codes currently in use (see `backend/shared/exceptions/error_codes.py`):

```
VALIDATION_ERROR
NOT_FOUND
UNAUTHORIZED
FORBIDDEN
CONFLICT
BAD_REQUEST
INTERNAL_ERROR

USER_ALREADY_EXISTS
INVALID_PASSWORD
INVALID_CREDENTIALS
INACTIVE_USER
INVALID_ACCESS_TOKEN
INVALID_REFRESH_TOKEN
```

See `docs/auth-runbook.md` for the full status/code table for the auth endpoints.

---

# API Rules

## Authentication

Protected endpoints require JWT token.

---

## Authorization

Users can only access their own:

- profile,
- conversations,
- messages,
- diet plans.

---

## Versioning

All endpoints are versioned:

```
/api/v1
```

---

# Future Extensions

Possible future endpoints:

```
/health-integrations

/shopping-lists

/recipes

/reports

/notifications
```