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

## Dietitian Context

Responsible for:

- dietitian applications,
- dietitian profiles, including uploaded photos.

Database:

```
PostgreSQL
```

Main entities:

```
DietitianApplication

DietitianProfile
```

---

## Admin Context

Responsible for:

- user account management (list/activate/ban/delete),
- dietitian-application review (approve/reject),
- marking a transaction paid/unpaid, and listing every transaction.

Database: **none.** This context has no domain entities or persistence
of its own — it's pure orchestration over the Identity, Dietitian, and
Transactions contexts' own repositories. Deliberately absent from the
Aggregates and Persistence Mapping sections below for that reason, not
by omission.

---

## Transactions Context

Responsible for:

- a user purchasing one of a dietitian's two fixed offers,
- tracking whether that purchase has been paid.

Database:

```
PostgreSQL
```

Main entities:

```
Transaction
```

No real payment gateway — an explicit demo-scope decision, the same
spirit as this project's Mock AI provider / Mailhog / local SFTP
stand-ins elsewhere. An admin manually marks a transaction paid/unpaid
(Admin Context, above).

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

role

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
- `role` (Phase 12) is one of `USER` (default for every new account),
  `DIET_USER`, `ADMIN`, `SUPER_ADMIN`. `User.change_role()` is a plain
  state transition + `UserRoleChanged` event — it does **not** itself
  enforce who may promote whom (e.g. "only `SUPER_ADMIN` may grant
  `ADMIN`"); that's an authorization concern enforced by the API layer's
  `require_role` dependency guarding whichever endpoint calls it, not a
  domain invariant about the entity's own state. There is no
  self-escalation path anywhere in the API — the only way to change a
  role is `PATCH /admin/users/{user_id}/role`, itself `SUPER_ADMIN`-only.

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

categories   — tuple of ConversationCategory, at least one, deduplicated

status

createdAt

updatedAt
```

---

## Conversation Rules

- Conversation belongs to one user.
- Conversation has at least one category — `create()` deduplicates repeats
  and rejects an empty list (`InvalidConversationError`); a conversation can
  be steered by more than one category at once (e.g. `DIET` + `RUNNING`).
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

weekly_obligations   — tuple of WeeklyObligation (Phase 9, see below)

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
When `weekly_obligations` is non-empty, it appends a "weekly commitments"
clause, which is also how that schedule reaches `DietPlanPromptBuilder`
(no separate parameter — see `DietPlan`/`Meal` below).

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
- `weekly_obligations` follows the same partial-update convention as every
  other field: omit it on `PUT /profile` to leave the schedule untouched,
  send `[]` to explicitly clear it (`None` vs. `()` are distinguishable).

---

## WeeklyObligation

Value Object (embedded in `NutritionProfile`, no identity of its own).
`modules/nutrition/domain/value_objects/weekly_obligation.py`. Phase 9.

A recurring weekly time block — work, training, or any other commitment
the user wants diet-plan generation to avoid scheduling meals into.

Example:

```
WeeklyObligation

day_of_week    — MON | TUE | WED | THU | FRI | SAT | SUN

start_time

end_time       — must be after start_time

label          — free text, e.g. "Work", "Training"
```

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

updated_at      — Phase 9; starts equal to created_at, moves only on reschedule_meal()
```

`create()` validates `duration_days` is between 1 and 14, that `days` has
exactly that many entries, and that no meal has a negative macro value.
Regenerating always produces a new `DietPlan` (a user can have many) — that
part hasn't changed. What changed in Phase 9: a plan is **not** fully
immutable anymore. `reschedule_meal(day_number, meal_name, new_time)` is
the one mutation it supports — everything else about a plan (macros, meal
identity, day count) still can't change after generation.

---

## DietPlan Rules

- `goal`/`diet_type` are not supplied by the caller — they come from the
  user's existing `NutritionProfile`; generating a plan without one first
  is rejected (mirrors `SendMessageUseCase`'s optional-profile personalization,
  except here a profile is *required*, not optional — a diet plan has no
  sensible default goal to fall back to).
- `len(days)` must equal `duration_days` exactly.
- No `Meal` may have a negative `calories`/`protein`/`carbohydrates`/`fat`.
- `reschedule_meal()` (Phase 9) locates the target day/meal and rebuilds
  the `Meal`/`DietDay`/`days` chain with the new time (via
  `dataclasses.replace` — the value objects it touches are frozen, so this
  is reconstruction, not in-place mutation of them); an unknown
  `day_number`/`meal_name` raises `MealNotFoundError`.

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

`day_number` has no calendar date of its own — `day_number = 1` is treated
as the plan's `created_at` date, counting forward, wherever a real date is
needed (conflict-clamping against `WeeklyObligation`, the CSV export's
`date` column). A one-line assumption if it ever needs to change.

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

time    — Phase 9; AI-suggested "HH:MM", nullable — the model isn't required
          to provide one, and Ollama in particular sometimes doesn't
```

No `description`/`ingredients` fields — kept to exactly what the AI
generates and what the API surfaces; not modeled as a nested `Ingredient`
value object (deferred — see Future Extensions).

`time` is suggested by the AI at generation and nudged away from any
`WeeklyObligation` it collides with (a bounded heuristic, not a full
scheduler — see architecture.md), then freely editable afterward via
`DietPlan.reschedule_meal()`.

---

## DietPlanExport

Entity. `modules/nutrition/domain/entities/diet_plan_export.py`. Phase 9.

Metadata for one CSV export of a `DietPlan`, archived on an SFTP server —
this entity itself holds no file content, only a pointer to it.

Example:

```
DietPlanExport

id

user_id

diet_plan_id

filename       — the archived file's name on the SFTP server

created_at
```

A plan can be exported more than once (e.g. after rescheduling a meal) —
each export is a distinct `DietPlanExport`/file, never an overwrite of a
previous one.

---

# 7. Dietitian Domain

## DietitianApplication

Aggregate Root.

A user's application to become a dietitian, reviewed by an admin.

Example:

```
DietitianApplication

id

userId

experience

diplomas

description

status

reviewedBy

reviewedAt

createdAt

updatedAt
```

Rules:

- one application per user, ever — enforced by a `UNIQUE` constraint on
  `userId`, not just an application-layer check; there is no
  reapply-after-rejection flow in this MVP scope,
- `status` is one of `PENDING` (default), `APPROVED`, `REJECTED`,
- `approve()`/`reject()` both guard via an internal `_assert_pending()`
  — an already-reviewed application cannot be reviewed a second time
  (`ApplicationAlreadyReviewedError`), a genuine invariant about the
  entity's own state, unlike `User.change_role()`'s authorization split,
- `experience`/`description` cannot be blank.

---

## DietitianProfile

Aggregate Root.

A dietitian's public-facing profile — created once an application is
approved (not yet automated; see `docs/implementation-roadmap.md`
Etap 2).

Example:

```
DietitianProfile

id

userId

experience

diplomas

description

photos

createdAt

updatedAt
```

Rules:

- one profile per user, ever (`UNIQUE` constraint on `userId`),
- `photos` holds at most 3 entries — `add_photo()` raises
  `PhotoLimitExceededError` beyond that; `remove_photo(index)` raises
  `InvalidDietitianProfileError` for an out-of-range index,
- `update_details()` changes only the given fields (same partial-update
  shape as `NutritionProfile.update_details()`),
- `experience`/`description` cannot be blanked out via `update_details()`,
- neither entity in this domain currently emits domain events (unlike
  `User.change_role()` → `UserRoleChanged`) — their state transitions
  are plain mutations for now; add events here if a future consumer
  (e.g. a notification on approval) needs to react to them.

---

# 8. Transactions Domain

## Transaction

Aggregate Root.

A user's purchase of one of a dietitian's two fixed offers.

Example:

```
Transaction

id

userId          — the buyer

dietitianId     — nullable: SET NULL if the dietitian account is later
                   deleted, so the buyer's own transaction history
                   survives (unlike userId, which is CASCADE — the
                   transaction disappears with its buyer)

offerType       — PLAN_REVIEW | INDIVIDUAL_PLAN

amount          — Decimal, server-computed from offerType, never
                   client-supplied

status          — UNPAID (default) | PAID

createdAt

paidAt          — set on mark_paid(), cleared on mark_unpaid()
```

Rules:

- `status` is a 2-state, admin-reversible **toggle**, not a one-way
  approval state machine like `DietitianApplication`'s
  `PENDING → APPROVED|REJECTED` — `mark_paid()`/`mark_unpaid()` are both
  idempotent, neither raises on a redundant call,
- `create()` rejects `userId == dietitianId` (a user cannot buy their
  own offer) — a pure data invariant, checked in the entity itself since
  it needs no repository lookup; confirming the *dietitian* side is
  actually a `DIET_USER` does need one and lives in the application
  layer instead,
- neither `mark_paid()` nor `mark_unpaid()` emits a domain event — the
  business event that matters (`TransactionPaid`, for Phase 12 Etap 5's
  Kafka consumer) is published through a separate
  `TransactionEventPublisher` port, not the domain-events list below,
  since it's cross-context (Admin context calls it, not this one) and
  currently a no-op (see docs/architecture.md).

---

# 9. AI Domain

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

categories   — tuple of strings, one or more; a conversation with several
              categories folds guidance for all of them into one systemPrompt

systemPrompt

conversationHistory
```

`systemPrompt` is fully composed by `PromptBuilder` (dietetics/fitness framing +
per-category guidance for every category on the conversation + user profile,
once folded in) — providers just pass it through as-is, rather than each
building their own system message from raw category/profile fields.

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

# 10. Aggregates

Current aggregate roots:

```
User

Conversation

NutritionProfile

DietPlan

DietitianApplication

DietitianProfile

Transaction
```

Rules:

- aggregate roots control their internal state,
- external objects cannot modify aggregate internals directly.

---

# 11. Domain Events

Possible domain events:

```
UserRegistered

UserLoggedIn

PasswordChanged

EmailVerified

UserRoleChanged

ProfileCreated

ProfileUpdated

ConversationCreated

MessageAdded

DietPlanGenerated
```

Domain events represent important business facts.

---

# 12. Relationships

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

`User` also has an at-most-one relationship to each of
`DietitianApplication` and `DietitianProfile` (both `UNIQUE` on
`userId`), omitted from the diagram above to keep it to the original
chat/nutrition flow — see the Dietitian Domain section for their shape.

`User` also has a **many** relationship to `Transaction` on both sides —
once as a buyer (`userId`, `ON DELETE CASCADE`) and once as a dietitian
(`dietitianId`, `ON DELETE SET NULL`) — the only relationship in this
model where the same entity plays two different roles with two
different delete behaviors. See the Transactions Domain section above.

---

# 13. Persistence Mapping

## PostgreSQL

Identity context:

```
users

refresh_tokens

password_reset_tokens

email_verification_tokens

email_logs
```

Dietitian context:

```
dietitian_applications

dietitian_profiles
```

Transactions context:

```
transactions
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

diet_plan_exports   — Phase 9; metadata only, files live on SFTP
```

---

# 14. Domain Rules

The following rules must always be respected:

1. Business rules belong to the domain layer.

2. Database models are not domain models.

3. External services are accessed through abstractions.

4. Modules do not directly access each other's persistence.

5. New business capabilities should be added inside the correct bounded context.

6. Domain objects should not depend on frameworks.

---

# 15. Future Extensions

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

Already in progress (Phase 12, see `docs/implementation-roadmap.md`):
admin panel + roles (Etap 0, done), dietitian applications and profile
management (Etap 1, done), the admin backend module + `frontend-admin`
app (Etap 2, done), fixed-price dietitian-offer transactions (this
domain — Etap 3, done through Stage 4), reviews, marketplace, and a
Kafka-backed human chat with dietitians (Etaps 4-6, not yet started).

These should be introduced only when supported by real business requirements.