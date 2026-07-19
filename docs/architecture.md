# Diet AI - Architecture

## 1. Overview

Diet AI is an AI-powered nutrition assistant that allows users to communicate with an AI model and receive personalized dietary recommendations.

The system allows users to:

- create an account,
- authenticate,
- configure their nutrition profile,
- communicate with AI through chat,
- generate diet recommendations,
- store conversation history,
- analyze previous interactions.

The main goal of the project is to build a production-quality backend application using modern software architecture practices.

---

# 2. Architecture Goals

The architecture is designed around the following principles:

- Domain Driven Design (DDD)
- Hexagonal Architecture
- Modular Monolith
- Separation of business logic and infrastructure
- Testability
- Easy replacement of external services
- Clear module boundaries

The system should be easy to extend with future features such as:

- mobile application,
- additional AI providers,
- health integrations,
- nutrition tracking,
- background processing.

---

# 3. Architectural Style

The project uses a **Modular Monolith** architecture.

The application is a single deployable backend, but internally consists of independent business modules.

```
Diet AI Backend

+--------------------------------+

| Identity Module                |
|                                |
| Conversation Module            |
|                                |
| Nutrition Module               |
|                                |
| AI Module                      |
|                                |
| Reporting Module               |

+--------------------------------+
```

Each module owns:

- its business logic,
- its domain model,
- its application services,
- its infrastructure adapters.

The modules are designed so they could be extracted into separate services in the future if required.

---

# 4. Why Modular Monolith?

The project is developed by a single developer.

A microservice architecture would introduce unnecessary complexity:

- network communication,
- deployment complexity,
- distributed transactions,
- additional infrastructure.

A modular monolith provides:

- simple development,
- easier debugging,
- faster iteration,
- clear boundaries.

The architecture keeps future extraction into microservices possible.

---

# 5. Hexagonal Architecture

Each module follows Hexagonal Architecture.

General structure:

```
Module

├── api
│
├── application
│
├── domain
│
└── infrastructure
```

---

## API Layer

Responsible for:

- HTTP communication,
- request validation,
- authentication handling,
- DTO mapping.

The API layer does not contain business logic.

---

## Application Layer

Responsible for:

- use cases,
- application workflows,
- coordination between domain objects.

Examples:

```
RegisterUserUseCase

LoginUserUseCase

SendMessageUseCase

GenerateDietPlanUseCase
```

---

## Domain Layer

Contains the business logic.

Responsible for:

- entities,
- value objects,
- aggregates,
- domain services,
- domain rules.

The domain layer must not depend on:

- FastAPI,
- databases,
- external APIs,
- frameworks.

---

## Infrastructure Layer

Contains technical implementations.

Responsible for:

- database access,
- external API communication,
- authentication providers,
- AI providers.

Infrastructure implements interfaces defined by the application/domain layer.

### Shared Kernel (`backend/shared/`)

Cross-cutting code with **no dependency on any single module's domain** —
config, database session factories, the exception/error-response
machinery, request-ID middleware, logging setup, and (Phase 8) two new
small packages:

- `shared/security/` — `SecureToken` (see Identity Module above) and
  `hash_password`/`verify_password` (plain bcrypt wrappers). Identity's own
  `BcryptPasswordHasher` still lives in identity's infrastructure layer and
  delegates to these — it implements identity's own `PasswordHasher` port,
  so the class itself can't move to `shared` without creating a
  shared-depends-on-module dependency in the wrong direction; only the
  dependency-free primitive underneath it moved.
- `shared/utils/` — `build_model_from_schema`/`build_example_from_schema`
  (JSON-Schema-subset → Pydantic model conversion), moved here from the AI
  module's Ollama integration once it became clear the functions have zero
  coupling to `Prompt`/`AIResponse` or anything Ollama-specific — they only
  ever touched `dict`/`type[BaseModel]`.

The dependency direction only ever goes one way: a module may depend on
`shared/`, `shared/` never depends on a module. That's the test applied
before moving anything here — a `domain/services/` file that reaches into
a module's own entities or exceptions stays in that module, no matter how
generic its logic looks on the surface (e.g. identity's `PasswordPolicy`
looks like a generic string-validation helper, but it raises identity's
own `InvalidPasswordError` directly, so it stays put).

---

# 6. High Level Architecture

```
                     Frontend

                         |

                         |

                    FastAPI API

                         |

        +----------------+----------------+

        |                |                |

   Identity        Conversation      Nutrition

        |                |                |

 PostgreSQL        MongoDB          MongoDB


                         |

                         |

                      AI Module

                         |

                Claude Provider / Ollama (local)
```

---

# 7. Application Modules

## Identity Module

Responsible for user identity and access management.

Responsibilities:

- registration (with an email verification token issued and sent on sign-up),
- authentication,
- JWT handling,
- refresh tokens,
- logout (single-session refresh token revocation),
- password reset,
- email verification,
- email delivery logging + retry for failed sends,
- user account management.

Database:

PostgreSQL

Technology:

- SQLAlchemy
- Alembic

Main entities:

```
User                     — gained email_verified: bool (Phase 8)

RefreshToken

PasswordResetToken       — Phase 8: 30 min TTL, single use

EmailVerificationToken   — Phase 8: 24h TTL, single use

EmailLog                 — Phase 8: audit trail for every send attempt
                            (metadata + delivery status only — never the
                            email body, see below)
```

### Secure one-time tokens (password reset & email verification)

Both `PasswordResetToken` and `EmailVerificationToken` follow the same
shape: mint a random opaque secret (`secrets.token_urlsafe(32)`), persist
only its SHA-256 hash, hand the raw secret to the caller exactly once (in
the email body) and never again. This generation/hashing logic is
identical for both token types, so it's factored into a single shared
class, `SecureToken` (`generate() -> (raw, hash)`, `hash(raw) -> hash`) —
see "Shared Kernel" below for where it actually lives.

`ConfirmPasswordResetUseCase` additionally calls
`RefreshTokenRepository.revoke_all_for_user()` after a successful reset —
every other session is forced to re-authenticate, standard practice after
a credential change. Email verification does **not** gate login:
`LoginUserUseCase` is untouched by `email_verified` — this is a deliberate
scope boundary, not an oversight; verifying email is tracked but not
enforced.

### EmailSender, Mailhog, and the delivery log

`EmailSender` (`application/ports/email_sender.py`) is a port with two
implementations — `MockEmailSender` (default, `EMAIL_PROVIDER=mock`, an
in-memory list, used in tests) and `SmtpEmailSender` (`EMAIL_PROVIDER=smtp`,
real `aiosmtplib` delivery). Local dev points `SmtpEmailSender` at a
Mailhog container (`docker-compose.yml`'s `mailhog` service, SMTP on 1025,
web UI + HTTP API on 8025) — a local SMTP catcher, not a real mail
provider; nothing is ever sent externally in dev.

`EmailSender.send(to, subject, body, purpose)` takes a `purpose` string
(`"PASSWORD_RESET"` / `"EMAIL_VERIFICATION"`) used only for the audit log
below, not for routing.

Every send attempt is wrapped by `LoggingEmailSender` (decorator over the
base sender) which records an `EmailLog` row — `SENT` on success, `FAILED`
with the exception message on failure — then re-raises on failure so the
existing propagate-to-500 behavior for a broken send is unchanged, just
now audited. **The email body is deliberately never persisted** — a
reset/verification email carries a raw one-time secret in its body, and
persisting it would defeat the entire point of only ever storing a hash
(see "Secure one-time tokens" above). `email_logs` has no FK to `users` —
a log entry must outlive the user it was sent to.

`EmailSender`/`LoggingEmailSender` are constructed **per request**, not as
an app-lifetime singleton like `LLMProvider` or the Mongo client — despite
following the same "swappable provider behind a port" pattern. The
difference: `LoggingEmailSender` needs a request-scoped Postgres session to
write its `EmailLog` row, matching every other Postgres-backed repository
in this module, and `aiosmtplib` was already observed to open/close a
connection per `send()` call, so there was never a real resource worth
pooling across requests.

### Failed-email retry

A `FAILED` `EmailLog` row isn't necessarily final. A background `asyncio`
task (`infrastructure/email/email_retry_scheduler.py`, started via
`asyncio.create_task` in `main.py`'s `lifespan()`, no broker/queue library
added — a single periodic job doesn't justify one) polls every
`EMAIL_RETRY_INTERVAL_SECONDS` (default 180s) for rows due a retry, up to
`EMAIL_RETRY_MAX_ATTEMPTS` (default 10) attempts, after which the row stays
permanently `FAILED`.

Retrying does **not** resend the original body (there isn't one persisted
to resend — see above). Instead, `RetryFailedEmailsUseCase` looks the user
up again by `to` and asks a purpose-keyed `EmailRetryStrategy`
(`PasswordResetRetryStrategy` / `EmailVerificationRetryStrategy`) to mint
and persist a **brand-new** token for the same purpose, then sends that.
This preserves the "never persist a secret" invariant even under retry,
at the cost of the user needing to use the newest email if more than one
attempt was made. The retry use case sends via the **base** `EmailSender`,
not `LoggingEmailSender` — it owns updating the existing `EmailLog` row
itself (`attempts`, `next_retry_at`), so wrapping it again would create a
duplicate row per attempt instead of tracking the original one.

---

# Conversation Module

Responsible for AI conversations.

Responsibilities:

- creating conversations,
- storing messages,
- maintaining chat history,
- communication workflow with AI,
- archiving conversations (Phase 8 — a conversation's existing
  `Conversation.archive()` domain method had no API route before this),
- deleting conversations (Phase 8).

Database:

MongoDB

Technology:

- Beanie ODM (`beanie==2.1.0`) — integrated. `shared/database/mongo.py` uses
  PyMongo's native async client (`pymongo.AsyncMongoClient`), not Motor: Beanie 2.x
  requires it (MongoDB deprecated Motor in favor of PyMongo's own async API, and
  Beanie 2.x calls a driver-metadata hook that only exists on the new client).
  Nutrition (see below) uses the same Beanie setup, so Mongo access is
  consistent across both modules.

Main entities:

```
Conversation   — status: ACTIVE | ARCHIVED

Message
```

`POST /conversations/{id}/archive` sets `status = ARCHIVED`: still readable
via `GET`, but `POST .../messages` on an archived conversation now raises
`ArchivedConversationError` → `409 Conflict`. `DELETE /conversations/{id}`
is a hard delete of the conversation and its full message history — no
soft-delete flag, no undo.

**Multiple categories per conversation (pre-frontend addendum).** A
conversation is no longer steered by a single `ConversationCategory` — it
now carries `categories: tuple[ConversationCategory, ...]`, at least one,
deduplicated at `create()` time (`InvalidConversationError` on an empty
list). `PromptBuilder` folds every selected category's guidance into one
system prompt instead of looking up a single entry, so a conversation
tagged `DIET` + `RUNNING` gets both sets of guidance at once. Driven by the
frontend's "Nowy czat" category picker moving from single- to multi-select.

---

# Nutrition Module

Responsible for nutrition-related business logic.

Responsibilities:

- nutrition profile (implemented),
- user goals (implemented, part of the profile),
- weekly recurring obligations — work/training hours (implemented — Phase 9),
- diet generation (implemented — Phase 7),
- meal recommendations (implemented, as part of diet generation),
- AI-suggested + user-editable meal scheduling (implemented — Phase 9),
- CSV export of a plan, archived for later re-download (implemented — Phase 9).

Database:

MongoDB (Beanie, same client/setup as Conversation — see above).

Technology:

- Beanie ODM, `nutrition_profiles` collection with a unique index on
  `user_id` (one profile per user, enforced at the DB layer); `diet_plans`
  collection with a compound `(user_id, created_at)` index (a user can have
  many plans, and Phase 9 added date-range filtering on `created_at`
  alongside the existing `user_id` match — see below); `diet_plan_exports`
  collection with a non-unique index on `diet_plan_id` (a plan can be
  exported more than once).

Main entities:

```
NutritionProfile   — age, height_cm, weight_kg, activity_level, goal,
                     diet_type, weekly_obligations (Phase 9)

WeeklyObligation   — Phase 9, embedded in NutritionProfile: day_of_week,
                     start_time, end_time, label — a recurring weekly time
                     block (work, training, ...) fed into diet-plan
                     generation so meals get scheduled around it

DietPlan           — id, user_id, goal, diet_type, duration_days,
                     requirements, days, created_at, updated_at (Phase 9)

DietDay / Meal     — embedded value objects inside DietPlan (day_number +
                     meals; name/calories/protein/carbohydrates/fat/
                     time [Phase 9, AI-suggested, nullable]) — not
                     separate collections

DietPlanExport     — Phase 9: id, user_id, diet_plan_id, filename,
                     created_at — metadata only; the actual CSV lives on
                     the SFTP server, not in Mongo
```

Status: `NutritionProfile` CRUD (`GET`/`POST`/`PUT /profile`) is implemented
and wired into the AI module — `SendMessageUseCase` looks up the caller's
profile and folds `NutritionProfile.as_prompt_text()` into the system prompt
via `PromptBuilder`, so chat responses are personalized when a profile
exists (chatting still works fine with no profile set).

`POST /diet-plans/generate` (Phase 7) is also implemented: it requires an
existing `NutritionProfile` (404 otherwise — a diet plan has no meaningful
default without a goal/diet type to seed it from), builds a structured
prompt via `ai.application.DietPlanPromptBuilder`, and calls
`LLMProvider.generate_structured_response()` — a second `LLMProvider` method
(alongside `generate_response`) added specifically for this, since a diet
plan needs reliable structured JSON rather than free-text chat prose. See
the AI Module section below for how each provider implements it.

## Weekly obligations & AI-suggested meal scheduling (Phase 9)

Originally a "diet plan is generate-only, there's no update" module — Phase
9 added a pre-frontend calendar feature: meals show up like calendar
appointments (day + time), AI suggests the time, the user can edit it
afterward.

`NutritionProfile.weekly_obligations` is a tuple of `WeeklyObligation`
(day-of-week + start/end time + label) that the profile owner maintains via
the existing `PUT /profile` (partial-update semantics: omitting the field
leaves the schedule untouched, sending `[]` clears it). `as_prompt_text()`
appends a "weekly commitments" clause when any exist, so the diet-plan
prompt already carries this context without a second, duplicate parameter.

`DietPlanPromptBuilder.build_schema()`'s meal item gained an optional
`"time"` string property (`"HH:MM"`, **not** in `"required"` — a small
local model (Ollama) omitting it shouldn't hard-fail validation, per this
module's documented small-model reliability findings below). The system
prompt asks the model to suggest a time and schedule around any weekly
commitments mentioned in the profile text.

**Conflict-clamping (a code-level safety net, not full trust in the
model)**: after generation, `GenerateDietPlanUseCase` resolves each meal's
actual weekday via `MealScheduler.resolve_weekday(plan_start_date,
day_number)` — `day_number = 1` is treated as the plan's creation date,
counting forward (a deliberate assumption: "generate my plan starting
today"; the same assumption is reused for CSV date columns and the day
range shown in error messages). If the AI-suggested time falls inside a
`weekly_obligations` window for that weekday, `MealScheduler.clamp_meal_time`
shifts it to the obligation's end (a bounded-iteration heuristic that
handles back-to-back obligations without looping forever — not a full
constraint solver, good enough to avoid "lunch during your 9-to-5" but not
a promise of a globally optimal schedule). A malformed AI time string is
dropped (`Meal.time = None`) rather than failing the whole generation over
a cosmetic field.

**Rescheduling — the one mutation `DietPlan` ever undergoes.** Before
Phase 9, a `DietPlan` was fully immutable after `create()` — no
`updated_at` even existed, since nothing ever changed. `PATCH
/diet-plans/{id}/meals` → `DietPlan.reschedule_meal(day_number, meal_name,
new_time)` rebuilds the `Meal`/`DietDay`/`days` tuple chain (everything is
frozen value objects, so this is reconstruction via `dataclasses.replace`,
never in-place mutation) and bumps the now-meaningful `updated_at`. An
unknown day/meal raises `MealNotFoundError` → **400** (not 404 — the plan
itself exists and belongs to the caller; it's a sub-part of it that
doesn't, the same distinction `InvalidWeeklyObligationError` draws on the
profile side).

## CSV export, archived to SFTP (Phase 9)

Originally scoped as a stateless "generate CSV on request" endpoint;
revised (user request, mid-stage) so every export is durably archived —
the value being that a user can come back later and re-download a
previously generated export without regenerating it.

`application/ports/sftp_client.py` — `SftpClient` (`upload`/`download`), a
swappable external-delivery port shaped exactly like `EmailSender` in
Identity (Phase 8): a real implementation (`AsyncSshSftpClient`, via
`asyncssh` — consistent with this stack being async end-to-end: Mongo,
Postgres, SMTP) and a `MockSftpClient` selected by `SFTP_PROVIDER`
(`mock` default / `sftp` for `docker-compose.yml`, mirroring
`EMAIL_PROVIDER`). The mock is constructed fresh per request (like
`MockEmailSender`), so it does **not** persist uploads across requests —
documented directly in its docstring, since that's the opposite of this
feature's whole point; it exists only so the app boots without a live SFTP
connection.

`ExportDietPlanUseCase` builds the CSV (`application/csv_export.py` —
day_number, date [same day-1-is-creation-date assumption as
conflict-clamping], time, meal, macros), uploads it under a per-export
filename (`{plan_id}-{random suffix}.csv` — a plan can be exported more
than once, e.g. after a reschedule, and each export is its own file, never
an overwrite), and records a `DietPlanExport`. Download proxies
server-side (`SftpClient.download` → streamed back over HTTP) since SFTP
has no presigned-URL equivalent.

Local dev target: `docker-compose.yml`'s `sftp` service (`atmoz/sftp:alpine`,
user `dietai`/`dietai`), the same "swappable port + a real local Docker
target" shape as Mailhog for `EmailSender`. Unlike Mailhog, this image has
a real shell, so its healthcheck (`nc -z 127.0.0.1 22`) lets `backend`
depend on `service_healthy` rather than the weaker `service_started`.

**Test strategy, decided deliberately**: automated tests never touch a
real SFTP server. Use-case tests get a `FakeSftpClient` (in-memory dict,
`tests/fakes.py`) constructed once and reused across calls within a test
— unlike the production `MockSftpClient`, this one *does* need to survive
an export-then-download round trip inside a single test. API-level tests
override just the `get_sftp_client` FastAPI dependency with a shared
`FakeSftpClient` per test — the same pattern already used for
`get_email_sender` in Phase 8. Real persistence is only verified manually
against the real Docker stack, matching how Mailhog was never part of the
automated suite either.

## Date-range filtering for plan history (Phase 9)

`GET /diet-plans` gained optional `from`/`to` query params (ISO dates) —
purely an additive display filter, **not** a retention/auto-delete policy
(a deliberate decision: "let the user pick the range" themselves, nothing
gets deleted in the background). `DietPlanRepository.list_by_user_id`
gained matching optional `start_date`/`end_date` parameters; omitting both
keeps the exact prior behavior, so no existing caller broke. `end_date` is
inclusive of the whole calendar day (implemented as an exclusive upper
bound at the start of the *next* day, to sidestep any time-of-day
granularity question). The router validates `from <= to` itself (400
otherwise) — FastAPI's parameter name uses `Query(alias="from")` since
`from` is a reserved Python keyword and can't be a literal parameter name.

---

# AI Module

Responsible for communication with AI models.

The module provides an abstraction over AI providers.

Example:

```
LLMProvider

        |

        |

+-----------------+

| MockLLMProvider |

| ClaudeProvider  |

| OllamaProvider  |

+-----------------+
```

The rest of the application does not know which AI provider is used — selection
happens via `AI_PROVIDER` (`mock` | `claude` | `ollama`) through
`modules/ai/infrastructure/provider_factory.py`.

Status: implemented. `ClaudeProvider` (`infrastructure/anthropic/`) uses the
official `anthropic` SDK against Claude (default model `claude-opus-4-8`).
`OllamaProvider` (`infrastructure/ollama/`) talks to a self-hosted Ollama
container over its HTTP API directly via `httpx` — there's no official SDK for
this, so raw HTTP is the correct choice here, not a shortcut. Local dev
(`docker-compose.yml`) runs a real Ollama container with a small model
(`llama3.2:1b`, ~1.3GB) pulled automatically on first start. The former
temporary `MockLLMProvider` in `shared/providers/ai.py`, and the unused generic
`DIContainer` it was registered in, have both been deleted — nothing ever
consumed them for real.

## Structured output (`generate_structured_response`)

`LLMProvider` has a second method besides `generate_response`, added for
Phase 7's diet plan generation: `generate_structured_response(prompt,
schema) -> dict`, returning JSON validated against a caller-supplied JSON
Schema instead of free-text prose. Each provider implements it differently:

- **`ClaudeProvider`** — native structured outputs
  (`output_config: {"format": {"type": "json_schema", "schema": schema}}`
  on `messages.create()`), which guarantees schema-conformant JSON; no
  client-side validation needed.
- **`OllamaProvider`** — no native structured-output guarantee, so it:
  (1) sends `"format": "json"` (JSON-syntax-only guarantee), (2) renders a
  filled-in *example instance* of the schema into the prompt (not the raw
  schema definition — empirically, dumping raw JSON Schema syntax made
  `llama3.2:1b` echo the schema's own `type`/`properties` keys back as the
  "answer"; a concrete example is far more reliable for small models),
  (3) validates the response against a Pydantic model dynamically built
  from the schema (`shared/utils/schema_validation.py` — moved here from
  this module in Phase 8 once it became clear the conversion has zero
  Ollama-specific coupling, see "Shared Kernel" above), (4) retries **once**
  with the validation error appended to the prompt, then raises
  (fail loud — no silent fallback to a malformed plan). Even with the
  improved prompt, the small local model can still occasionally invent
  extra keys (especially when free-text `requirements` are present) and
  exhaust the retry — a real, accepted limitation of a 1B-parameter local
  model doing structured generation, not a bug to chase further; switching
  to `AI_PROVIDER=claude` avoids it entirely.
- **`MockLLMProvider`** — parses the requested day count back out of the
  prompt text and returns that many canned days, so it stays usable for
  manual end-to-end testing of the diet-plan endpoint without hitting a
  real model.

---

# Reporting Module

Future module responsible for:

- statistics,
- summaries,
- reports.

Possible features:

- nutrition progress,
- chat statistics,
- generated reports.

---

# 8. Persistence Strategy

The system uses **Polyglot Persistence**.

Different databases are used for different types of data.

---

## PostgreSQL

Used for transactional and relational data.

Responsible for:

- users,
- authentication,
- permissions,
- sessions.

Reason:

Relational databases provide:

- strong consistency,
- constraints,
- transactions,
- indexing.

---

## MongoDB

Used for document-oriented data.

Responsible for:

- conversations,
- messages,
- AI context,
- diet plans.

Reason:

Documents better represent:

- conversation history,
- nested structures,
- AI-generated content.

---

# 9. Data Ownership Rules

Each module owns its data.

Rules:

- modules cannot directly access another module database,
- communication happens through application interfaces,
- domain logic cannot depend on persistence technology.

Example:

Incorrect:

```
Conversation module

↓

Identity PostgreSQL table
```

Correct:

```
Conversation module

↓

Identity application interface

↓

Identity module
```

---

# 10. AI Communication Flow

Example chat flow:

```
User

↓

Frontend

↓

Conversation API

↓

SendMessageUseCase

↓

Conversation Domain

↓

Prompt Builder

↓

LLM Provider

↓

AI Model

↓

Save Response

↓

MongoDB
```

---

# 11. Configuration

Application configuration is managed externally.

Sources:

```
.env

↓

Application Settings

↓

Dependency Injection
```

Sensitive data must never be stored in code.

Examples:

- database passwords,
- API keys,
- JWT secrets.

---

# 12. Docker

The application should be runnable locally using Docker Compose.

Actual services (`docker-compose.yml`, as of Phase 10 — this list was a
sparse Phase 0 draft before and had drifted; several services were added
since):

```
backend

frontend    — React + Vite dev server (Phase 10, the actual web UI)

db          — PostgreSQL (Identity)

mongo       — MongoDB (Conversation, Nutrition)

ollama      — local LLM (default AI_PROVIDER)

mailhog     — local SMTP catcher (Phase 8, password reset/email verification)

sftp        — local SFTP server (Phase 9, diet-plan CSV export archive)
```

Example:

```
docker compose up
```

---

# 13. Future Extensions

Possible future improvements:

- Redis cache,
- message broker,
- background workers,
- vector database,
- semantic search,
- AI memory,
- mobile application,
- external health integrations.

These should only be introduced when required by the system.

---

# 14. Architecture Rules

The following rules should always be respected:

1. Business logic belongs to the domain layer.

2. Controllers should remain simple.

3. Use cases represent application actions.

4. Infrastructure implements technical details.

5. External services are accessed through abstractions.

6. Modules own their data.

7. Frameworks must not define the domain model.

8. New features should be added inside existing modules or new bounded contexts.

---

# 15. Summary

Diet AI is designed as a modular backend application using:

- Python,
- FastAPI,
- Hexagonal Architecture,
- Domain Driven Design,
- PostgreSQL,
- MongoDB,
- AI provider abstraction.

The architecture intentionally balances professional software engineering practices with simplicity suitable for a single-developer project.