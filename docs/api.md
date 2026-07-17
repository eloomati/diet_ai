# Diet AI - API Contract

## Overview

This document defines the REST API contract for the Diet AI application.

The API provides functionality for:

- user registration and authentication,
- nutrition profile management,
- AI conversations,
- conversation history,
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
  "status": "ACTIVE"
}
```

### Errors

401 Unauthorized — `INVALID_ACCESS_TOKEN` (missing/malformed/expired token, or token references a deleted user)

403 Forbidden — `INACTIVE_USER`

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

## GET /profile

Returns authenticated user's nutrition profile.

Authentication:

Required.

### Response

```json
{
  "id": "uuid",
  "age": 29,
  "height": 187,
  "weight": 80,
  "activityLevel": "HIGH",
  "goal": "MUSCLE_GAIN",
  "dietType": "VEGETARIAN"
}
```

---

## POST /profile

Creates nutrition profile.

### Request

```json
{
  "age": 29,
  "height": 187,
  "weight": 80,
  "activityLevel": "HIGH",
  "goal": "MUSCLE_GAIN",
  "dietType": "VEGETARIAN"
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
  "id": "uuid",
  "createdAt": "2026-01-01T10:00:00Z"
}
```

---

## PUT /profile

Updates nutrition profile.

### Request

```json
{
  "weight": 82,
  "activityLevel": "VERY_HIGH"
}
```

### Response

```
200 OK
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

---

# Diet Plan API

Module:

```
Nutrition
```

---

## POST /diet-plans/generate

Generates personalized diet plan using AI.

### Request

```json
{
  "goal": "MUSCLE_GAIN",
  "durationDays": 7,
  "requirements": [
    "high protein",
    "vegetarian breakfast"
  ]
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
  "id": "diet-plan-id",
  "durationDays": 7,
  "days": [
    {
      "day": 1,
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
  ]
}
```

---

## GET /diet-plans

Returns generated diet plans.

### Response

```json
[
  {
    "id": "diet-plan-id",
    "goal": "MUSCLE_GAIN",
    "createdAt": "2026-01-01T10:00:00Z"
  }
]
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