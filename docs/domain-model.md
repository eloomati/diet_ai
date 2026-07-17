# Diet AI - Domain Model

## 1. Purpose

This document describes the business domain model of Diet AI.

The goal is to define:

- bounded contexts,
- domain entities,
- aggregates,
- value objects,
- domain responsibilities.

The domain model is independent from:

- FastAPI,
- PostgreSQL,
- MongoDB,
- SQLAlchemy,
- Beanie,
- external AI providers.

---

# 2. Domain Overview

The system is divided into bounded contexts.

```
+----------------+

| Identity       |

+----------------+

        |

+----------------+

| Conversation   |

+----------------+

        |

+----------------+

| Nutrition      |

+----------------+

        |

+----------------+

| AI             |

+----------------+

```

Each context owns its own business rules and data.

---

# 3. Bounded Contexts

## Identity Context

Responsible for:

- user account,
- authentication,
- authorization.

Database:

```
PostgreSQL
```

Main entities:

```
User

RefreshToken
```

---

## Conversation Context

Responsible for:

- chat conversations,
- messages,
- conversation history.

Database:

```
MongoDB
```

Main entities:

```
Conversation

Message
```

---

## Nutrition Context

Responsible for:

- nutrition profile,
- dietary goals,
- generated diet plans.

Database:

```
MongoDB
```

Main entities:

```
NutritionProfile

DietPlan

Meal
```

---

## AI Context

Responsible for:

- communication with AI models,
- prompt generation,
- AI response handling.

The AI context is stateless.

---

# 4. Identity Domain

## User

Aggregate Root.

The User represents an account in the system.

Responsibilities:

- authentication identity,
- account lifecycle,
- ownership of resources.

Example:

```
User

id

email

passwordHash

status

emailVerified

createdAt

updatedAt
```

---

## User Rules

Business rules:

- email must be unique,
- password cannot be stored as plain text,
- inactive users cannot authenticate,
- `emailVerified` is tracked but does not gate authentication — a
  deliberate scope boundary (Phase 8), not an oversight.

---

## RefreshToken

Entity.

Responsible for maintaining user sessions.

Example:

```
RefreshToken

id

userId

tokenHash

expiresAt

createdAt

revoked
```

---

## PasswordResetToken

Entity. (Phase 8)

A single-use, time-limited credential that authorizes exactly one password
change.

Example:

```
PasswordResetToken

id

userId

tokenHash

expiresAt

used

createdAt
```

Rules:

- `issue()` mints a random opaque secret (`secrets.token_urlsafe(32)`) and
  returns it alongside the entity — the entity itself only ever stores the
  secret's SHA-256 hash (`tokenHash`), never the plaintext,
- TTL defaults to 30 minutes,
- `is_valid()` is false once `used` or once `expiresAt` has passed,
- a successful confirm calls `mark_used()` **and** revokes every refresh
  token belonging to the user (see `RefreshToken` above) — a password
  change forces re-login everywhere.

---

## EmailVerificationToken

Entity. (Phase 8)

Same shape and secret-generation mechanism as `PasswordResetToken` (both
delegate to the shared `SecureToken` service — see `docs/architecture.md`),
issued at registration instead of on a reset request.

Example:

```
EmailVerificationToken

id

userId

tokenHash

expiresAt

used

createdAt
```

Rules:

- TTL defaults to 24 hours — verification is far less time-sensitive than
  a password reset,
- confirming sets `User.emailVerified = true` but does **not** change
  anything about the user's ability to log in.

---

## EmailLog

Entity. (Phase 8)

An audit trail of every email the application attempted to send —
metadata and delivery status only.

Example:

```
EmailLog

id

to

subject

purpose

status        — SENT | FAILED

attempts

nextRetryAt

errorMessage

createdAt
```

Rules:

- **the email body is never stored** — a reset/verification email carries
  a raw one-time secret in its body, and this entity's entire purpose
  (auditing) would otherwise defeat the "never persist the secret" rule
  that `PasswordResetToken`/`EmailVerificationToken` are built around,
- no foreign key to `User` — a log entry must survive the deletion of the
  user it was sent to,
- a `FAILED` row is retried up to `EMAIL_RETRY_MAX_ATTEMPTS` times (default
  10, every `EMAIL_RETRY_INTERVAL_SECONDS` = 180s) by re-minting a fresh
  token of the same purpose (never resending the original, unstored,
  body) — once exhausted, `nextRetryAt` is cleared and the row stays
  `FAILED` permanently.

---

# 5. Conversation Domain

## Conversation

Aggregate Root.

Represents a conversation between user and AI.

Responsibilities:

- owns messages,
- manages conversation lifecycle,
- stores conversation context.

Example:

```
Conversation

id

userId

title

category

status

createdAt

updatedAt
```

---

## Conversation Rules

- Conversation belongs to one user.
- Messages cannot exist without a conversation.
- Archived conversations cannot receive new messages.

---

# Message

Entity.

Represents a single communication entry.

Example:

```
Message

id

role

content

createdAt

tokenUsage
```

Roles:

```
USER

ASSISTANT

SYSTEM
```

---

## Message Rules

- Messages are immutable after creation.
- Message order is based on creation time.
- Message belongs only to one Conversation.

---

# 6. Nutrition Domain

## NutritionProfile

Aggregate Root. Implemented in `modules/nutrition/domain/entities/nutrition_profile.py`.

Represents user nutrition information.

This entity does NOT belong to Identity because it represents business information related to nutrition, not authentication.

Example:

```
NutritionProfile

id

user_id

age

height_cm

weight_kg

activity_level

goal

diet_type

created_at

updated_at
```

Field names spell out units (`height_cm`, `weight_kg`) rather than bare
`height`/`weight` — cheap insurance against metric/imperial mixups on health
data.

`as_prompt_text()` renders the profile as a plain-string summary, consumed by
`ai.PromptBuilder` when composing the AI system prompt (see Conversation
Domain / AI Module in architecture.md) — decoupled from the `ai` module the
same way `Message.role` stays a plain value rather than a shared type.

---

## NutritionProfile Rules

- profile belongs to one user — enforced by a unique index on `user_id` at
  the persistence layer (one profile per user; `POST` a second time is a 409,
  not a silent overwrite — use `PUT` to update).
- `age` must be between 1 and 120.
- `height_cm` must be between 50 and 250.
- `weight_kg` must be between 20 and 400.
- Validation runs both on `create()` and on `update()` (a partial update
  re-validates the merged result, not just the changed fields).

---

# DietGoal

Value Object. Implemented in `modules/nutrition/domain/value_objects/diet_goal.py`.

Represents user's nutrition objective.

Values:

```
WEIGHT_LOSS

MUSCLE_GAIN

MAINTENANCE

PERFORMANCE
```

Sibling value objects: `ActivityLevel` (`LOW | MODERATE | HIGH | VERY_HIGH`)
and `DietType` (`STANDARD | VEGETARIAN | VEGAN | KETO | PALEO | GLUTEN_FREE`).

---

# DietPlan

Aggregate Root. Implemented in `modules/nutrition/domain/entities/diet_plan.py`.

Represents an AI-generated, structured multi-day diet plan.

Example:

```
DietPlan

id

user_id

goal            — copied from the user's NutritionProfile at generation time

diet_type       — copied from the user's NutritionProfile at generation time

duration_days

requirements    — tuple of free-text hints supplied at generation time

days            — tuple of DietDay

created_at
```

A plan is immutable once generated — there is no `update()`; regenerating
produces a new `DietPlan` (a user can have many). `create()` validates
`duration_days` is between 1 and 14, that `days` has exactly that many
entries, and that no meal has a negative macro value.

---

## DietPlan Rules

- `goal`/`diet_type` are not supplied by the caller — they come from the
  user's existing `NutritionProfile`; generating a plan without one first
  is rejected (mirrors `SendMessageUseCase`'s optional-profile personalization,
  except here a profile is *required*, not optional — a diet plan has no
  sensible default goal to fall back to).
- `len(days)` must equal `duration_days` exactly.
- No `Meal` may have a negative `calories`/`protein`/`carbohydrates`/`fat`.

---

# DietDay

Value Object (embedded in `DietPlan`, no identity of its own).
`modules/nutrition/domain/value_objects/diet_day.py`.

Represents one day of a diet plan.

Example:

```
DietDay

day_number     — 1-indexed

meals          — tuple of Meal
```

---

# Meal

Value Object (embedded in `DietDay`, no identity of its own).
`modules/nutrition/domain/value_objects/meal.py`.

Represents a single meal within a day.

Example:

```
Meal

name

calories

protein

carbohydrates

fat
```

No `description`/`ingredients` fields — kept to exactly what the AI
generates and what the API surfaces; not modeled as a nested `Ingredient`
value object (deferred — see Future Extensions).

---

# 7. AI Domain

The AI context provides abstraction over external AI systems.

---

# LLMProvider

Domain Port.

Example:

```
LLMProvider

generateResponse(prompt)
```

Implementations:

```
MockLLMProvider   (deterministic, no network — default in dev/tests)

ClaudeProvider    (Anthropic, via the official SDK)

OllamaProvider    (self-hosted, via raw HTTP — no official SDK exists for it)
```

Selected at runtime via `AI_PROVIDER` config (`mock` | `claude` | `ollama`).

---

# Prompt

Value Object.

Represents complete context sent to AI.

Example:

```
Prompt

question

category

systemPrompt

conversationHistory
```

`systemPrompt` is fully composed by `PromptBuilder` (dietetics/fitness framing +
per-category guidance + user profile, once folded in) — providers just pass it
through as-is, rather than each building their own system message from raw
category/profile fields.

---

# AIResponse

Value Object.

Represents AI result.

Example:

```
AIResponse

content

model

tokens

executionTime
```

---

# 8. Aggregates

Current aggregate roots:

```
User

Conversation

NutritionProfile

DietPlan
```

Rules:

- aggregate roots control their internal state,
- external objects cannot modify aggregate internals directly.

---

# 9. Domain Events

Possible domain events:

```
UserRegistered

UserLoggedIn

PasswordChanged

EmailVerified

ProfileCreated

ProfileUpdated

ConversationCreated

MessageAdded

DietPlanGenerated
```

Domain events represent important business facts.

---

# 10. Relationships

High-level relationship diagram:

```
User

 |

 |

 +--------------------+

 |                    |

Conversation      NutritionProfile

 |

 |

Message


NutritionProfile

 |

 |

DietPlan

 |

 |

Meal

```

---

# 11. Persistence Mapping

## PostgreSQL

Identity context:

```
users

refresh_tokens

password_reset_tokens

email_verification_tokens

email_logs
```

---

## MongoDB

Conversation context:

```
conversations
```

Nutrition context:

```
nutrition_profiles

diet_plans
```

---

# 12. Domain Rules

The following rules must always be respected:

1. Business rules belong to the domain layer.

2. Database models are not domain models.

3. External services are accessed through abstractions.

4. Modules do not directly access each other's persistence.

5. New business capabilities should be added inside the correct bounded context.

6. Domain objects should not depend on frameworks.

---

# 13. Future Extensions

Possible future domain extensions:

```
FoodDiary

Recipe

ShoppingList

TrainingPlan

HealthIntegration

BodyMeasurementHistory

AllergyProfile
```

These should be introduced only when supported by real business requirements.