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
  "password": "password123"
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
  "email": "user@example.com",
  "createdAt": "2026-01-01T10:00:00Z"
}
```

### Errors

400 Bad Request

```json
{
  "code": "INVALID_EMAIL",
  "message": "Email format is invalid"
}
```

409 Conflict

```json
{
  "code": "USER_ALREADY_EXISTS",
  "message": "User with this email already exists"
}
```

---

## POST /auth/login

Authenticates a user.

### Request

```json
{
  "email": "user@example.com",
  "password": "password123"
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
  "accessToken": "jwt-token",
  "refreshToken": "refresh-token",
  "expiresIn": 3600
}
```

### Errors

401 Unauthorized

```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "Invalid email or password"
}
```

---

## POST /auth/refresh

Creates a new access token using refresh token.

### Request

```json
{
  "refreshToken": "refresh-token"
}
```

### Response

```json
{
  "accessToken": "new-jwt-token",
  "expiresIn": 3600
}
```

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

## POST /conversations

Creates a new conversation.

### Request

```json
{
  "category": "DIET",
  "title": "High protein breakfasts"
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
  "id": "conversation-id",
  "category": "DIET",
  "createdAt": "2026-01-01T10:00:00Z"
}
```

---

## GET /conversations

Returns conversations belonging to authenticated user.

### Response

```json
[
  {
    "id": "conversation-id",
    "title": "High protein breakfasts",
    "category": "DIET",
    "updatedAt": "2026-01-01T12:00:00Z"
  }
]
```

---

## GET /conversations/{id}

Returns conversation history.

### Response

```json
{
  "id": "conversation-id",
  "title": "High protein breakfasts",
  "category": "DIET",
  "messages": [
    {
      "id": "message-id",
      "role": "USER",
      "content": "Create breakfast ideas",
      "createdAt": "2026-01-01T10:01:00Z"
    },
    {
      "id": "message-id",
      "role": "ASSISTANT",
      "content": "Here are ideas...",
      "createdAt": "2026-01-01T10:01:05Z"
    }
  ]
}
```

---

## POST /conversations/{id}/messages

Sends user message and generates AI response.

### Request

```json
{
  "message": "I run 5 times a week. Create high protein breakfasts for 7 days."
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
  "messageId": "uuid",
  "answer": "Here is your weekly breakfast plan...",
  "createdAt": "2026-01-01T10:02:00Z"
}
```

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

Available categories:

```
DIET

FITNESS

RUNNING

HEALTH

SUPPLEMENTS

GENERAL
```

Categories influence:

- prompt generation,
- AI context,
- future business rules.

---

# Common Error Format

All API errors use the same structure.

```json
{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "timestamp": "2026-01-01T10:00:00Z"
}
```

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