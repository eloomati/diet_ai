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
Phase 2  - Database Setup           DONE (Postgres + Mongo/Beanie both wired; Beanie
                                     currently only registers Conversation's document —
                                     Nutrition's collections still pending Phase 4)
Phase 3  - Identity Module          DONE (register, login, refresh, me; JWT; unified
                                     error format; real-DB + fake-based tests)
Phase 4  - User Profile (Nutrition) NOT STARTED (empty skeleton only)
Phase 5/6 - Conversation + AI       IN PROGRESS — domain, application, Mongo
                                     persistence, and LLM providers done
                                     (Stages 1-4: Mock/Claude/Ollama, not
                                     OpenAI — see Stage 4). API layer + full
                                     integration tests remain (Stages 5-6)
Phase 7+ - Diet Generation/Frontend/Testing/Future  NOT STARTED
```

Current milestone: **Conversation + AI ("chat MVP")** — see the detailed
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

## Stage 2 — Application (use cases, tested against in-memory fakes) — DONE

`modules/conversation/application/`:
- [x] `use_cases/create_conversation_use_case.py`
- [x] `use_cases/send_message_use_case.py` — builds the `Prompt` from history
      *before* appending the new user `Message` (avoids duplicating the current
      question inside `conversation_history`), calls
      `LLMProvider.generate_response`, appends assistant `Message`, saves, returns.
- [x] `use_cases/get_conversation_history_use_case.py`
- [x] `use_cases/list_conversations_use_case.py` — added beyond the original
      list; needed to back `GET /conversations` (list) separately from
      `GET /conversations/{id}` (single, with full message history) in Stage 5.
- [x] `dto/` — commands/results per use case (same shape as Identity's `dto/`).
      Deviation from the original plan: skipped a `ports/` re-export package —
      Identity's own use cases import `UserRepository` straight from `domain`,
      not from an application-level re-export, so conversation use cases do the
      same for `ConversationRepository`. No `PromptBuilderPort` either —
      `PromptBuilder` is a stateless static-method service (same shape as
      Identity's `PasswordPolicy`), not an external system needing an
      abstraction.
- [x] Ownership check: `SendMessageUseCase`/`GetConversationHistoryUseCase` both
      raise `ConversationNotFoundError` for a conversation that doesn't exist
      *or* doesn't belong to the requesting user (same "don't leak existence"
      shape as Identity's login/refresh error handling).

`modules/ai/application/`:
- [x] `prompt_builder.py` — pure static-method service assembling `Prompt` from
      a `Conversation` + the new question; `user_profile` still left unset
      (Nutrition Profile doesn't exist yet).

`modules/conversation/tests/fakes.py`: `InMemoryConversationRepository`.
`modules/ai/tests/fakes.py`: `FakeLLMProvider` returning a canned response.

Exit criteria: use case tests pass against fakes only, no real DB/HTTP.
12 tests added, full suite at 82/82 passing.

---

## Stage 3 — Infrastructure: Mongo persistence for Conversation — DONE

- [x] **Beanie ODM** added (`beanie==2.1.0`). `Document`/`Message` map to
      `infrastructure/documents/conversation_document.py`'s `ConversationDocument`
      (embeds messages as a `MessageEmbedded` list — the natural fit, since
      messages are only ever read/written as part of their conversation,
      matching the aggregate boundary in domain-model.md).
- [x] `infrastructure/mappers/conversation_mapper.py` — Document ↔ domain
      entity mapping (mirrors identity's `UserMapper`; sets `domain_events=[]`
      on rehydration for the same reason `UserMapper` does).
- [x] `infrastructure/repository/mongo_conversation_repository.py` implementing
      `ConversationRepository`.
- [x] **Unplanned but required: dropped Motor, switched to pymongo's native
      async client (`pymongo.AsyncMongoClient`).** Beanie 2.x doesn't support
      Motor — MongoDB deprecated Motor in favor of PyMongo's own async API
      (added in PyMongo 4.9+), and Beanie 2.x calls a driver-metadata hook that
      only exists on the new client. `shared/database/mongo.py` rewritten
      accordingly; `motor` removed from `requirements.txt` (nothing else used it).
- [x] `backend/app/main.py` lifespan now always calls `init_mongo` +
      `init_beanie_documents([ConversationDocument])` — previously Mongo init
      was skipped when `settings.testing`, back when nothing used it; now
      Conversation needs it, so tests need a real Mongo too (see below).
- [x] Test isolation: extended `docker-compose.test.yml` with a `mongo-test`
      service (port 27018, `tmpfs` data dir, same ephemeral-container pattern
      as `db-test`) instead of retroactively mixing Motor and Beanie for Nutrition
      — Nutrition (Phase 4, still not started) should use the same Beanie setup
      once it starts, for consistency.
- [x] Added `backend/modules/conversation/tests/conftest.py` (same `client`
      fixture as Identity's, since Stage 5's API tests will need the full app).
      Repository-level tests use a *separate*, dedicated async fixture
      (`init_mongo`/`init_beanie_documents` called directly in the test's own
      event loop) rather than the `client`/TestClient fixture — pymongo's async
      client is bound to the event loop it was created in, and TestClient runs
      the app's lifespan in its own separate loop/thread, so a repository test
      awaiting Mongo calls directly would hit
      `RuntimeError: Cannot use AsyncMongoClient in different event loop`.
- [x] Rebuilt the `backend` Docker image (`docker compose up -d --build backend`)
      — the running dev container had `beanie` missing until rebuilt, since
      only `requirements.txt` on the host had changed, not the baked image.

Exit criteria: repository-level tests against a real (ephemeral, Dockerized)
Mongo — same isolation approach as `docker-compose.test.yml` for Postgres.
4 tests added, full suite at 86/86 passing.

---

## Stage 4 — Infrastructure: real LLM provider — DONE

**Scope change from the original plan:** OpenAI → **Claude (Anthropic)**, plus a
third provider — **Ollama**, self-hosted in its own container — added at the
same time rather than deferred, per updated requirements.

- [x] `modules/ai/infrastructure/providers/mock_llm_provider.py` — moved the
      logic out of the now-deleted `shared/providers/ai.py`, behind
      `LLMProvider`. Returns a deterministic canned `AIResponse`; default
      dev/test provider (`AI_PROVIDER=mock`).
- [x] `modules/ai/infrastructure/anthropic/claude_provider.py` — `ClaudeProvider`
      using the official `anthropic` SDK (`AsyncAnthropic`), model defaults to
      `claude-opus-4-8` via `settings.anthropic_model`. Constructor accepts an
      injectable client for testing (fake object, no real network call in tests).
- [x] `modules/ai/infrastructure/ollama/ollama_provider.py` — `OllamaProvider`
      talking to a local/self-hosted Ollama server's HTTP API directly via
      `httpx.AsyncClient` (no official SDK exists for this — that's expected,
      not a shortcut). Same injectable-client pattern for tests.
- [x] **Prerequisite fix, done first:** `Prompt.conversation_history` changed
      from flat `"ROLE: content"` strings (Stage 2) to structured `PromptTurn(role,
      content)` tuples — the flat format would have forced every provider to
      re-parse it back into a role/content split. `PromptBuilder` and its Stage 2
      tests updated accordingly.
- [x] `Settings.use_mock_ai` (bool) replaced with `Settings.ai_provider: str`
      (`"mock" | "claude" | "ollama"`), plus `anthropic_api_key`, `anthropic_model`,
      `ollama_base_url`, `ollama_model`.
- [x] `modules/ai/infrastructure/provider_factory.py` — `build_llm_provider(settings)`
      picks the provider by `settings.ai_provider`; raises a clear `RuntimeError`
      for `claude` with no API key configured, rather than silently falling back
      to mock (a misconfigured "production" deployment should fail loudly, not
      quietly serve canned responses).
- [x] **Retired `shared/providers/` (`DIContainer`, `ai.py`) entirely** — nothing
      real ever consumed it (confirmed via grep before deleting); its
      `use_mock_ai` branch was already dead code (`MockLLMProvider() if
      use_mock_ai else MockLLMProvider()` — both branches were identical, a bug
      nobody hit because nothing called it). Removed `app.state.di_container`
      from `main.py`, deleted `backend/tests/test_di_container.py`, and trimmed
      the two DI-container assertions out of `test_app_startup.py` (its health-
      endpoint test stays).
- [x] `docker-compose.yml`: new `ollama` service (`ollama/ollama:latest`),
      auto-pulls `llama3.2:1b` (~1.3GB, CPU-friendly) on first start via its
      command, healthcheck waits for the model to actually be present (not just
      the server up). `backend` depends on it and defaults to `AI_PROVIDER=ollama`
      in Docker dev; `.env.example` documents all three provider configs.
      Verified end-to-end: real `POST /api/chat` round-trip against the running
      container returned actual generated text.

Exit criteria: `SendMessageUseCase` works end-to-end against all three providers
(mock in unit tests; Claude and Ollama unit-tested via injected fake clients, no
real network calls in the test suite), switchable via `AI_PROVIDER` only.
9 tests added, full suite at 90/90 passing.

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