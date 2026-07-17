# Diet AI - Implementation Roadmap

## Purpose

This document defines the implementation order of the Diet AI project.

The goal is to build the system incrementally while keeping architecture clean.

Each phase should result in a working part of the system.

---

## Status (as of 2026-07-17)

```
Phase 0  - Project Bootstrap        DONE
Phase 1  - Architecture Skeleton    DONE (module folders + hexagonal layout scaffolded)
Phase 2  - Database Setup           PARTIAL (Postgres done; Mongo connection exists,
                                     Beanie/collections not started)
Phase 3  - Identity Module          DONE (register, login, refresh, me; JWT; unified
                                     error format; real-DB + fake-based tests)
Phase 4  - User Profile (Nutrition) NOT STARTED (empty skeleton only)
Phase 5  - Conversation Module      NOT STARTED (empty router only)
Phase 6  - AI Integration           NOT STARTED (empty skeleton; a temporary
                                     MockLLMProvider lives in shared/providers/ai.py,
                                     unused by any real flow)
Phase 7+ - Diet Generation/Frontend/Testing/Future  NOT STARTED
```

Next planned milestone: **Conversation + AI ("chat MVP")** — see the detailed
sub-plan under Phase 5/6 below. Nutrition Profile (Phase 4) is deferred until
after it, since chatting with the AI doesn't strictly need profile personalization
for a first version (`Prompt.userProfile` can be added once Nutrition exists).

---

# Phase 0 - Project Bootstrap

Goal:

Create a working development environment.

## Tasks

### Repository

- [x] Create monorepo structure
- [x] Initialize Git repository
- [x] Create README
- [x] Create documentation structure

---

### Backend

- [x] Create Python project
- [x] Configure dependency management
- [x] Create FastAPI application
- [x] Configure application settings
- [x] Add environment variables support

Expected result:

```
GET /health

Response:

{
  "status": "ok"
}
```

---

### Docker

Create:

- [x] Backend container
- [x] PostgreSQL container
- [x] MongoDB container

Expected:

```
docker compose up
```

starts the whole environment.

---

# Phase 1 - Backend Architecture Skeleton

Goal:

Create application structure before implementing business logic.

## Create modules

```
modules/

identity/

conversation/

nutrition/

ai/
```

---

## Create Hexagonal Structure

Every module:

```
module/

api/

application/

domain/

infrastructure/
```

---

## Implement shared components

- [x] Configuration management
- [x] Dependency injection
- [x] Exception handling
- [x] Logging basics

---

# Phase 2 - Database Setup

Goal:

Prepare persistence layer.

---

# PostgreSQL

Used by Identity.

Tasks:

- [x] Configure SQLAlchemy
- [x] Configure database connection
- [x] Configure Alembic
- [x] Create first migration

Initial tables:

```
users

refresh_tokens
```

---

# MongoDB

Used by Conversation and Nutrition.

Tasks:

- [ ] Configure MongoDB connection
- [ ] Configure Beanie
- [ ] Create document models

Initial collections:

```
conversations

nutrition_profiles

diet_plans
```

---

# Phase 3 - Identity Module

Goal:

Implement authentication.

Database:

PostgreSQL

---

## Domain

Create:

```
User

RefreshToken
```

Implement:

- [x] User entity
- [x] Password hashing
- [x] User validation rules

---

## Application

Create use cases:

```
RegisterUserUseCase

LoginUserUseCase

RefreshTokenUseCase
```

---

## Infrastructure

Implement:

- [x] SQLAlchemy models
- [x] User repository
- [x] JWT provider
- [x] Password encoder

---

## API

Endpoints:

```
POST /auth/register

POST /auth/login

POST /auth/refresh

GET /auth/me   (added beyond original scope — required by /me tests and
                by any future module that needs "who is the current user")
```

---

Expected result:

User can:

- create account,
- login,
- receive JWT token,
- fetch their own identity via a bearer token.

Also done, beyond what this phase originally scoped: refresh token rotation with
reuse-detection, a unified `{code, message, timestamp}` error format across all
endpoints (including 422 validation and 500s), and tests running against an
ephemeral Dockerized Postgres instead of the dev database (see
`docs/auth-runbook.md`, `conftest.py`, `docker-compose.test.yml`).

---

# Phase 4 - User Profile

Goal:

Create nutrition-related user information.

Module:

Nutrition

Database:

MongoDB

---

## Domain

Create:

```
NutritionProfile
```

Fields:

```
age

height

weight

activityLevel

goal

dietType
```

---

## Application

Create:

```
CreateNutritionProfileUseCase

UpdateNutritionProfileUseCase

GetNutritionProfileUseCase
```

---

## API

Endpoints:

```
GET /profile

POST /profile

PUT /profile
```

---

# Phase 5/6 - Conversation + AI ("Chat MVP")

Goal:

The next milestone after Identity. Treated as one combined rollout because AI has
no real consumer without Conversation (see architecture.md section 10 — the AI
flow *is* `Conversation API -> SendMessageUseCase -> ... -> LLM Provider`), and
Conversation has no reason to exist yet without AI attached to it.

Modules touched: `conversation` (new real code) and `ai` (new real code,
replacing the temporary `shared/providers/ai.py` placeholder).

Requirement update: conversations must support a **category that steers the
conversation** (e.g. breakfast, running, gym — see Stage 1's
`ConversationCategory`), and conversation history must be persisted in Mongo
and be visible on the user's profile. For MVP this means: history is stored
and queryable via `GET /conversations` / `GET /conversations/{id}` (Stage 5);
the profile *view* composing Identity + Conversation (+ later Nutrition) data
is a frontend concern for now — no new backend aggregation endpoint, per
architecture.md's module-ownership rule (modules don't reach into each other's
database; a cross-module "profile summary" endpoint, if needed later, belongs
in the future Reporting module, not bolted onto Identity or Conversation).

Follows the roadmap's own rule — Domain → Application → Infrastructure → API →
Tests — split into small, independently reviewable/testable stages, mirroring how
the Identity module was actually built (domain first, fakes-based unit tests
before touching real infrastructure, real-infra integration tests last).

---

## Stage 1 — Domain (no DB, no HTTP, unit-testable in isolation) — DONE

`modules/conversation/domain/`:
- [x] `entities/conversation.py` — `Conversation` aggregate: `id`, `user_id`, `title`,
      `category`, `status`, `created_at`, `updated_at`; rule: archived conversations
      reject new messages (mirrors `User.assert_can_authenticate` style guard).
- [x] `entities/message.py` — `Message` entity: `id`, `role` (`USER`/`ASSISTANT`/`SYSTEM`),
      `content`, `created_at`, `token_usage`; immutable after creation.
- [x] `value_objects/conversation_category.py` — closed enum, guides/steers the
      conversation (used in the `Prompt` sent to the AI): `GENERAL`, `DIET`,
      `BREAKFAST`, `FITNESS`, `RUNNING`, `GYM`, `HEALTH`, `SUPPLEMENTS`. Plain
      enum on purpose (not a dynamic/CRUD-managed entity) — adding a category
      later is a one-line code change + PR, matches docs/api.md's category list.
- [x] `exceptions/conversation_domain_errors.py` — e.g. `ArchivedConversationError`.
- [x] `repositories/conversation_repository.py` — port (ABC), no implementation yet.
- [x] `value_objects/conversation_status.py`, `value_objects/message_role.py`,
      `events/conversation_events.py` (`ConversationCreated`, `MessageAdded`) —
      added beyond the original list, mirroring Identity's `UserStatus` +
      `user_events.py` pattern.

`modules/ai/domain/`:
- [x] `ports/llm_provider.py` — `LLMProvider` ABC: `generate_response(prompt: Prompt) -> AIResponse`.
- [x] `value_objects/prompt.py` — `Prompt` (`system_context`, `conversation_history`,
      `category`, `question`; `user_profile` left as `None`/optional for now —
      wired once Nutrition Profile exists). `category` is a plain `str`, not
      `ConversationCategory`, to keep the `ai` domain decoupled from `conversation`
      — the application-layer `PromptBuilder` (Stage 2) converts the enum.
- [x] `value_objects/ai_response.py` — `AIResponse` (`content`, `model`, `tokens`, `execution_time`).

Exit criteria: unit tests for entities/value objects/domain rules, zero infra deps.
10 tests added (`test_conversation_entity.py`, `test_message_entity.py`,
`test_ai_value_objects.py`), full suite at 70/70 passing.

---

## Stage 2 — Application (use cases, tested against in-memory fakes)

`modules/conversation/application/`:
- [ ] `ports/` — re-export domain repository port + a `PromptBuilderPort` if useful.
- [ ] `use_cases/create_conversation_use_case.py`
- [ ] `use_cases/send_message_use_case.py` — loads conversation, appends user
      `Message`, builds a `Prompt` from history + category + question, calls
      `LLMProvider.generate_response`, appends assistant `Message`, saves, returns.
- [ ] `use_cases/get_conversation_history_use_case.py`
- [ ] `dto/` — commands/results per use case (same shape as Identity's `dto/`).

`modules/ai/application/`:
- [ ] `prompt_builder.py` — pure function/service assembling `Prompt` from a
      `Conversation` + latest user message (+ optional nutrition profile later).

`modules/conversation/tests/fakes.py`: `InMemoryConversationRepository`.
`modules/ai/tests/fakes.py` (or alongside conversation fakes): `FakeLLMProvider`
returning a canned/deterministic response — exactly the identity module's
`fakes.py` pattern, so use cases are tested fully before Mongo/OpenAI exist.

Exit criteria: use case tests pass against fakes only, no real DB/HTTP.

---

## Stage 3 — Infrastructure: Mongo persistence for Conversation

- [ ] **Decided: Beanie ODM** (external requirement — must use an ODM, not raw
      Motor, for Mongo access). Add `beanie` to `requirements.txt`, initialize
      it (`Document.init_beanie(...)`) alongside the existing `init_mongo` in
      `backend/app/main.py`'s lifespan.
- [ ] `infrastructure/documents/conversation_document.py` — Beanie `Document`
      subclass mapping `Conversation` + embedded `Message` list (embedding is
      the natural fit here: messages are only ever read/written as part of
      their conversation, matching the aggregate boundary in domain-model.md).
- [ ] `infrastructure/mappers/conversation_mapper.py` — Document ↔ domain
      entity mapping (mirrors identity's `UserMapper`; domain layer stays free
      of Beanie per architecture.md's layering rules).
- [ ] `infrastructure/repository/mongo_conversation_repository.py` implementing
      `ConversationRepository`.
- [ ] Same ODM approach should retroactively apply to Nutrition (Phase 4,
      still not started) once that phase starts — keep Mongo access consistent
      across modules rather than mixing raw Motor and Beanie.

Exit criteria: repository-level tests against a real (ephemeral, Dockerized)
Mongo — same isolation approach as `docker-compose.test.yml` for Postgres.

---

## Stage 4 — Infrastructure: real LLM provider

- [ ] `modules/ai/infrastructure/providers/mock_llm_provider.py` — move the
      logic currently in `shared/providers/ai.py` here for real, behind
      `LLMProvider`. Keep it as the default dev/test provider.
- [ ] `modules/ai/infrastructure/openai/openai_provider.py` — real provider;
      add `openai` to `requirements.txt`; use `settings.openai_api_key`.
- [ ] Provider selection already has a toggle in `Settings.use_mock_ai` — wire
      it into whatever builds the `LLMProvider` for `SendMessageUseCase`
      (today `use_mock_ai` only feeds the unused generic `DIContainer`; needs
      to actually reach the conversation use case's dependency wiring).
- [ ] Retire `shared/providers/ai.py` and `DIContainer` once the real wiring
      exists (currently registered but nothing consumes it).

Exit criteria: `SendMessageUseCase` works end-to-end against both providers
(mock in tests/dev, OpenAI behind a real key), switchable via config only.

---

## Stage 5 — API layer

Endpoints (per docs/api.md):

```
POST /conversations
GET /conversations
GET /conversations/{id}
POST /conversations/{id}/messages
```

- [ ] `api/schemas/` — request/response models.
- [ ] `api/dependencies/` — mirrors identity's `auth_dependencies.py` shape.
- [ ] `api/routers/conversation_router.py` — reuses Identity's
      `get_current_user` dependency for auth (no new auth mechanism).
- [ ] Errors raised as `AppException` with proper `ErrorCode`s from the start
      (no repeat of the "generic HTTPException" gap fixed in Identity).

---

## Stage 6 — Tests & docs

- [ ] Fakes-based unit tests (already covered in Stage 2) + real-Mongo
      integration tests (Stage 3) + full API integration tests (register →
      login → create conversation → send message → get history), same shape
      as `test_auth_api.py`.
- [ ] Update `docs/api.md`, `architecture.md`, `domain-model.md`, and this
      roadmap's status table as each stage actually lands — don't let this
      drift the way the Identity docs did before this review.

---

Expected result:

User can:

- create conversation,
- send messages and get an AI response,
- see history.

---

# Phase 7 - Diet Generation

Goal:

Generate personalized diets.

Module:

Nutrition

---

## Domain

Create:

```
DietPlan

DietDay

Meal
```

---

## Application

Create:

```
GenerateDietPlanUseCase
```

---

Example:

User:

```
I run 5 times a week.
Create high protein breakfasts for 7 days.
```

System:

```
Nutrition Profile

+

Conversation Context

+

AI

↓

Diet Plan
```

---

# Phase 8 - Frontend

Goal:

Create user interface.

Technology:

React

---

## Authentication

Implement:

- [ ] Login page
- [ ] Registration page
- [ ] JWT handling

---

## Chat

Implement:

- [ ] Chat window
- [ ] Message history
- [ ] Category tiles

Categories:

```
Diet

Fitness

Health

Running

Supplements
```

---

# Phase 9 - Testing

Goal:

Ensure application quality.

---

## Unit Tests

Test:

- Domain entities
- Value objects
- Use cases

---

## Integration Tests

Test:

- Database repositories
- API endpoints

---

## End-to-End Tests

Test:

```
Register

↓

Login

↓

Create Profile

↓

Send Chat

↓

Receive AI Response
```

---

# Phase 10 - Future Improvements

Only after MVP.

---

## Background Processing

Possible:

- task queue
- scheduled reports
- email notifications

---

## Cache

Possible:

Redis

Use cases:

- frequently requested profiles
- generated diets

---

## Messaging

Possible:

Kafka / RabbitMQ

Use cases:

```
DietGenerated

↓

SendEmail

↓

CreateReport

```

---

## AI Improvements

Possible:

- local LLM
- vector database
- semantic search
- AI memory

---

# MVP Definition

The first complete version is finished when:

- [x] User can register
- [x] User can login
- [ ] User can create nutrition profile
- [ ] User can start conversation
- [ ] User can chat with AI
- [ ] Conversation history is stored
- [ ] User can generate a simple diet plan

---

# Development Rule

Always implement in this order:

```
Domain

↓

Application

↓

Infrastructure

↓

API

↓

Tests
```

Do not start from controllers.

The domain should drive the implementation.