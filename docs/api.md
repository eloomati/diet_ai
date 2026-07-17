# Diet AI - API Contract

## Overview

This document defines the REST API contract for the Diet AI application.

The API provides functionality for:

- user registration and authentication,
- password reset and email verification,
- nutrition profile management,
- AI conversations,
- conversation history, archiving, and deletion,
- diet plan generation.

Base URL:

```
/api/v1
```

Authentication:

Protected endpoints require JWT authentication:

```
Authorization: Bearer {access_token}
```

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
  "password": "StrongPass123"
}
```

Password: 8-128 characters, must satisfy `PasswordPolicy` (see domain-model.md).

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

422 Unprocessable Entity — `VALIDATION_ERROR` (malformed email / missing fields)

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
  "email_verified": false
}
```

### Errors

401 Unauthorized — `INVALID_ACCESS_TOKEN` (missing/malformed/expired token, or token references a deleted user)

403 Forbidden — `INACTIVE_USER`

---

## POST /auth/password-reset/request

Issues a password reset token (30 min TTL) and emails it to the given
address, if an account with that address exists. Always returns the same
generic `200` regardless — this endpoint never reveals whether the email
is registered.

### Request

```json
{
  "email": "user@example.com"
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
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

### Errors

None — always `200`, whether or not the email exists.

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
  "diet_type": "VEGETARIAN"
}
```

Validation: `age` 1-120, `height_cm` 50-250, `weight_kg` 20-400 (422
`VALIDATION_ERROR` otherwise).

### Response

Status:

```
201 Created
```

Body: same shape as `GET /profile`.

Errors:

```
409 Conflict code=CONFLICT — profile already exists for this user
```

---

## PUT /profile

Partially updates the authenticated user's nutrition profile — only the
provided fields change, the rest are kept as-is.

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

Creates a new conversation.

### Request

```json
{
  "title": "High protein breakfasts",
  "category": "BREAKFAST"
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
  "category": "BREAKFAST",
  "status": "ACTIVE"
}
```

### Errors

401 Unauthorized — missing/invalid token (see auth-runbook.md)

422 Unprocessable Entity — `VALIDATION_ERROR` (invalid `category`, empty `title`)

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
    "category": "BREAKFAST",
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
  "category": "BREAKFAST",
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

All endpoints below require `Authorization: Bearer {access_token}` and a
nutrition profile must already exist for the caller (`POST /profile` —
see Nutrition Profile API above). `goal` and `diet_type` are **not**
request fields — they're read from the caller's existing
`NutritionProfile`, the same way chat responses are personalized from it.

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
          "fat": 15
        }
      ]
    }
  ],
  "created_at": "2026-01-01T10:00:00Z"
}
```

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

## GET /diet-plans

Lists the caller's own generated diet plans, newest first (summary only —
no `days`/`meals`).

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
    "created_at": "2026-01-01T10:00:00Z"
  }
]
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