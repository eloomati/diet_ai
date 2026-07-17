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
                                     registers Conversation, NutritionProfile, and
                                     DietPlan documents)
Phase 3  - Identity Module          DONE (register, login, refresh, me; JWT; unified
                                     error format; real-DB + fake-based tests)
Phase 4  - User Profile (Nutrition) DONE — profile CRUD wired into the AI
                                     prompt, verified end-to-end on the real
                                     Docker stack, docs/http fully synced.
Phase 5/6 - Conversation + AI       DONE — chat MVP is functional end-to-end
                                     (register → login → create conversation →
                                     send message → AI response → history),
                                     verified against the real Docker stack.
                                     Providers: Mock/Claude/Ollama, not OpenAI.
Phase 7  - Diet Generation          DONE — structured multi-day diet plan
                                     generation (POST /diet-plans/generate,
                                     GET /diet-plans, GET /diet-plans/{id}),
                                     verified end-to-end on the real Docker
                                     stack with Ollama. See the 6-stage log
                                     below, including a real reliability
                                     finding for the small local model.
Phase 8  - Conversation Lifecycle &  IN PROGRESS — post-Phase-7 gap audit
           Account Recovery          found no DELETE endpoints anywhere,
                                     no route to the domain's existing
                                     Conversation.archive(), and no password
                                     recovery path. Scope: conversation
                                     delete+archive, and password reset with
                                     real SMTP delivery via a new Mailhog
                                     dev container. See the 5-stage
                                     breakdown below.
Phase 9+ - Frontend/Testing/Future  NOT STARTED
```

**Phases 3 through 7 are complete** — Identity, Nutrition Profile,
Conversation + AI chat, and Diet Plan generation all work end-to-end against
the real Docker stack, with docs (`architecture.md`, `domain-model.md`,
`api.md`, `docs/https/*.http`) and `README.md` synced to match. Phase 8+
(Frontend, broader Reporting) is next — see that section below for the
sparse original draft, not yet split into stages.

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

# Phase 4 - User Profile (Nutrition)

Goal:

Create nutrition-related user information — and, unlike the original sparse
draft below, actually **wire it into the AI prompt**, since that's the whole
reason this was deferred behind the chat MVP: `PromptBuilder.build()` already
accepts an optional `user_profile: str | None` (added in Stage 2/4 of Phase
5/6) specifically for this moment.

Module: `nutrition`. Database: MongoDB (Beanie, same setup as Conversation).

Split into stages the same way as Phase 5/6 — Domain → Application →
Infrastructure → API → wire into AI → Tests/docs — each independently
reviewable, following the roadmap's own Development Rule.

---

## Stage 1 — Domain — DONE

`modules/nutrition/domain/`:
- [x] `entities/nutrition_profile.py` — `NutritionProfile` aggregate root:
      `id`, `user_id`, `age`, `height_cm`, `weight_kg`, `activity_level`,
      `goal`, `diet_type`, `created_at`, `updated_at`. Field names spell out
      units (`height_cm`, `weight_kg`) rather than the doc's bare
      `height`/`weight` — cheap insurance against metric/imperial mixups on
      health data.
- [x] `value_objects/activity_level.py` — enum: `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`.
- [x] `value_objects/diet_goal.py` — enum (from domain-model.md's `DietGoal`):
      `WEIGHT_LOSS`, `MUSCLE_GAIN`, `MAINTENANCE`, `PERFORMANCE`.
- [x] `value_objects/diet_type.py` — enum: `STANDARD`, `VEGETARIAN`, `VEGAN`,
      `KETO`, `PALEO`, `GLUTEN_FREE`.
- [x] `exceptions/nutrition_domain_errors.py` — `NutritionDomainError`,
      `InvalidNutritionProfileError` — enforces domain-model.md's "weight and
      height must have valid values" rule (sane bounded ranges, not just "not
      negative") at `create()`/`update()` time, same shape as Identity's
      `PasswordPolicy`-raises-on-`create()` pattern.
- [x] `repositories/nutrition_profile_repository.py` — port: `get_by_user_id`,
      `save`. One profile per user — enforced here at the repository/DB layer
      (Stage 3 unique index), not by a numeric identity check.
- [x] `NutritionProfile.as_prompt_text()` — a plain-string summary method,
      decoupled from the `ai` module (same reasoning as `Prompt.category`
      being a `str`, not an enum, to keep `ai` domain-independent).

Exit criteria: unit tests for the entity's validation rules and value objects,
zero infra deps. 10 tests added, full suite at 121/121 passing.

---

## Stage 2 — Application — DONE

`modules/nutrition/application/`:
- [x] `dto/` — commands/results per use case.
- [x] `use_cases/create_nutrition_profile_use_case.py` — rejects a second
      profile for the same user (`NutritionProfileAlreadyExistsError`) —
      creating twice should be a 409, not a silent overwrite; use `PUT` to update.
- [x] `use_cases/update_nutrition_profile_use_case.py` — partial update
      (only provided fields change), re-validates the merged result.
- [x] `use_cases/get_nutrition_profile_use_case.py` — raises
      `NutritionProfileNotFoundError` if the user never created one.
- [x] `tests/fakes.py` — `InMemoryNutritionProfileRepository`, same shape as
      Identity's/Conversation's.

Exit criteria: use case tests pass against fakes only, no real DB/HTTP.
7 tests added, full suite at 128/128 passing.

---

## Stage 3 — Infrastructure: Mongo persistence (Beanie) — DONE

- [x] `infrastructure/documents/nutrition_profile_document.py` — Beanie
      `Document`, `Settings.name = "nutrition_profiles"` (matches
      domain-model.md's persistence mapping), **unique index on `user_id`** —
      the DB-level backstop for "one profile per user" alongside the
      application-layer check.
- [x] `infrastructure/mappers/nutrition_profile_mapper.py` — Document ↔ domain,
      `domain_events=[]` on rehydration (same reasoning as `UserMapper`/`ConversationMapper`).
- [x] `infrastructure/repository/mongo_nutrition_profile_repository.py`.
- [x] Register `NutritionProfileDocument` in `main.py`'s
      `init_beanie_documents([ConversationDocument, NutritionProfileDocument])`.

Exit criteria: repository-level tests against the real ephemeral Mongo
(`docker-compose.test.yml`, same isolation as Conversation's Stage 3),
including a test that the unique index actually rejects a second profile for
the same user at the DB level. Verified on the real dev Mongo too
(`unique: true` on `ix_nutrition_profiles_user_id`). 4 tests added, full
suite at 132/132 passing.

---

## Stage 4 — API layer — DONE

Endpoints (per docs/api.md, updated to snake_case to match the rest of the API):

```
GET /profile
POST /profile
PUT /profile
```

- [x] `api/schemas/nutrition_schemas.py` — enums typed directly on the request
      model, same as Conversation's `category` (invalid value → 422
      `VALIDATION_ERROR` before it reaches the use case).
- [x] `api/dependencies/nutrition_dependencies.py` — mirrors Conversation's shape.
- [x] `api/routers/nutrition_router.py` + top-level `api/router.py` — reuses
      `get_current_user`. `POST` → `AppException(CONFLICT)` on duplicate;
      `GET`/`PUT` → `AppException(NOT_FOUND)` if no profile exists yet.

Exit criteria: full API integration tests (create → get → update → duplicate
create rejected → get-without-profile 404), same shape as `test_auth_api.py`.
**Deviation from the original draft**: endpoints are `/profile` with no
`/nutrition` segment (matches docs/api.md's documented contract) — the
pre-scaffolded `nutrition/api/router.py` had a stray `prefix="/nutrition"`
from Phase 1's skeleton that would have produced `/api/v1/nutrition/profile`
instead; removed it. 10 tests added, full suite at 142/142 passing. Verified
end-to-end on the real Docker stack too (create → get → update → duplicate 409).

---

## Stage 5 — Wire into the AI prompt (the actual point of this phase) — DONE

- [x] `SendMessageUseCase` gains a `NutritionProfileRepository` dependency,
      looks up the requesting user's profile (if any — chatting must still
      work with no profile set), and passes
      `user_profile=profile.as_prompt_text()` into `PromptBuilder.build()`.
- [x] `conversation_dependencies.get_send_message_use_case` wires the new
      repository dependency (`get_nutrition_profile_repository`) alongside the
      existing conversation repo + LLM provider — cross-module DI, `conversation`
      depends on `nutrition`'s domain port + Mongo implementation directly
      (one-directional; `nutrition` has no knowledge of `conversation`).
- [x] `FakeLLMProvider` (ai module test double) gained a `last_prompt` attribute
      so tests can assert on the exact composed `Prompt` a use case produced,
      not just the canned response.
- [x] Tests: `test_send_message_includes_nutrition_profile_in_prompt` (profile
      text appears in `Prompt.system_prompt` when one exists) and
      `test_send_message_without_nutrition_profile_still_works` (no profile ⇒
      still succeeds, no crash) — both exercised through the real
      `SendMessageUseCase`, not `PromptBuilder` directly. 2 tests added, full
      suite at 144/144 passing.
- [x] Manual end-to-end smoke test against the real Docker stack (Ollama):
      created a profile (`VEGAN`, `WEIGHT_LOSS`, `LOW` activity), asked "What
      should I eat for dinner tonight?" in a `DIET` conversation — the model's
      answer was fully vegan (tempeh + roasted vegetables, no animal products
      or dairy anywhere), confirming the profile actually reaches the prompt.
      Repeated with a fresh user with **no** profile — request still succeeded
      (HTTP 201) with a generic (non-personalized) answer, confirming the
      optional-profile path doesn't break the base flow.

---

## Stage 6 — Tests & docs sync — DONE

- [x] `docs/https/nutrition.http` — same style as `user.http`/`conversation.http`
      (register → login → get-before-create 404 → create → get → duplicate
      409 → update → invalid-age 422 → no-token 401 → second-user isolation
      404 → Stage 5 check: send a message and confirm the profile reaches the
      AI). All 12 steps replayed manually against the real Docker stack and
      matched their documented expected status codes.
- [x] `docs/api.md` Nutrition Profile section rewritten to the shipped
      snake_case shape (real field names, enum value lists, actual error
      codes per endpoint) — the previous draft still had camelCase
      `height`/`weight`/`activityLevel` fields that were never shipped.
- [x] `architecture.md` — Nutrition Module section updated: marked
      `NutritionProfile` implemented (vs. `DietPlan`/`Meal` still future),
      documented the AI wiring from Stage 5, fixed the stale ASCII diagram
      that still said "OpenAI Provider / Local Model" instead of
      Claude/Ollama, and removed a leftover "Nutrition should adopt Beanie
      once its phase starts" note (it already has).
- [x] `domain-model.md` — `NutritionProfile`/`DietGoal` sections updated to
      the real field names (`height_cm`/`weight_kg`, not bare
      `height`/`weight`) and real enum values (`WEIGHT_LOSS`, not
      `WeightLoss`), plus the actual validation ranges and unique-per-user rule.
- [x] **Bug found and fixed while replaying `nutrition.http`**: `GET /profile`
      right after `POST /profile` returned `created_at`/`updated_at` with no
      UTC offset (e.g. `2026-07-17T19:53:38.983000`), while a value fresh
      from `update()` had one (`...+00:00`) — inconsistent ISO 8601
      timestamps in the same response depending on whether the value round-
      tripped through Mongo. Root cause: PyMongo returns naive UTC datetimes
      by default, clashing with the rest of the app's `datetime.now(UTC)`
      convention. Fixed centrally in `shared/database/mongo.py` by passing
      `tz_aware=True` to `AsyncMongoClient` — benefits Conversation's
      timestamps too, not just Nutrition's. Verified via full pytest
      (144/144) and a live re-check on the Docker stack (both timestamps now
      consistently carry `+00:00`).
- [x] Roadmap status table updated (this file).

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
      a `Conversation` + the new question. **Revised post-Stage-4**: now builds
      a real system prompt (not just a bare "helpful assistant" line) —
      dietetics/fitness framing + a professional-advice disclaimer, plus
      per-category guidance (`SUPPLEMENTS` gets an explicit caution, `RUNNING`
      gets endurance-nutrition framing, etc). This also fixed a duplication bug:
      `ClaudeProvider` and `OllamaProvider` had each independently rebuilt an
      almost-identical system message from `Prompt.category`/`user_profile`
      /`system_context` — that's now composed once, in `PromptBuilder`, into a
      single `Prompt.system_prompt` field both providers just pass through.
      `build()` already accepts an optional `user_profile: str | None` so
      Nutrition (Phase 4, not started yet) only needs to add one call-site line
      in `SendMessageUseCase` once it exists — verified end-to-end against the
      real Ollama container that the richer prompt changes actual answers
      (e.g. a `SUPPLEMENTS`-category question about creatine came back with
      dosing specifics and a "consult a professional" section, not generic text).

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

## Stage 5 — API layer — DONE

Endpoints (per docs/api.md, now matching the actual shipped shape — snake_case,
not the original aspirational camelCase draft):

```
POST /conversations
GET /conversations
GET /conversations/{conversation_id}
POST /conversations/{conversation_id}/messages
```

- [x] `api/schemas/conversation_schemas.py` — request/response models.
      `CreateConversationRequest.category` is typed as the `ConversationCategory`
      enum directly, so an invalid value is rejected by pydantic (422
      `VALIDATION_ERROR`) before it ever reaches the use case.
- [x] `api/dependencies/conversation_dependencies.py` — mirrors identity's
      `auth_dependencies.py` shape, but simpler: Beanie/Mongo doesn't need a
      per-request session dependency the way `get_db_session` does for
      Postgres, so these just construct `MongoConversationRepository()` and
      `build_llm_provider(get_settings())` directly.
- [x] `api/routers/conversation_router.py` + top-level `api/router.py`
      (mirrors identity's nested `router.py` → `routers/auth_router.py` split)
      — reuses Identity's `get_current_user` dependency for auth (no new auth
      mechanism).
- [x] Errors raised as `AppException` with `ErrorCode.NOT_FOUND` from the start
      (no repeat of the "generic HTTPException" gap fixed in Identity).
      `ConversationNotFoundError` (doesn't exist *or* isn't yours) maps to a
      single 404 — same "don't leak existence" shape as Identity's login/refresh.

Verified two ways: 8 new API integration tests (register → login → create →
list → send message → get history → cross-user 404s), and a manual end-to-end
smoke test against the real running Docker stack (Postgres + Mongo + Ollama) —
a real `llama3.2:1b`-generated breakfast suggestion came back through the full
stack, not a mock.

Exit criteria met. Full suite at 98/98 passing.

---

## Stage 6 — Tests & docs

- [x] Fakes-based unit tests (Stage 2) + real-Mongo integration tests (Stage 3)
      + real-provider unit tests with injected fakes (Stage 4) + full API
      integration tests (Stage 5) are all in place already — Stage 6 is mainly
      the final docs-sync pass.
- [x] `docs/api.md` Conversation section rewritten to match the shipped
      snake_case shape (done during Stage 5 to avoid the drift Identity's docs
      had before the earlier review).
- [ ] `architecture.md` and `domain-model.md` — spot-check for any remaining
      drift once Stage 6 formally starts.

---

Expected result:

User can:

- create conversation,
- send messages and get an AI response,
- see history.

---

# Phase 7 - Diet Generation

Goal:

Generate a personalized, structured multi-day diet plan (days → meals →
name/calories/protein/carbs/fat) using AI, seeded from the user's
`NutritionProfile` (goal, diet_type, activity_level) plus optional free-text
requirements (e.g. "high protein breakfasts", "vegetarian").

Module: `nutrition` (domain/application/persistence/API) + `ai` (provider
extension). Database: MongoDB (Beanie, same setup as `NutritionProfile`).

**Key design decision** (confirmed with user): unlike the free-text chat
flow, a diet plan must come back as reliable structured JSON, not prose to
parse client-side — the tiny local Ollama model (`llama3.2:1b`) especially
cannot be trusted to emit clean JSON on its own. `LLMProvider` gains a second
method, `generate_structured_response(prompt, schema) -> dict`, alongside
the existing free-text `generate_response`:
- `ClaudeProvider` — native structured outputs (`output_config.format` with
  a `json_schema`), via the official `anthropic` SDK — guarantees valid JSON
  matching the schema.
- `OllamaProvider` — Ollama's `format` request field (JSON mode) plus
  Pydantic validation on our side, with **one retry** (re-prompt including
  the validation error) if the first response doesn't validate — no
  schema-level guarantee at the Ollama layer, so validation must happen
  client-side.
- `MockLLMProvider` — returns a small canned structured dict matching
  whatever schema shape the test expects, for fakes-based unit tests.

Split into stages the same way as Phase 4 — Domain → Application →
AI-provider extension → Mongo persistence → API → Tests/docs.

---

## Stage 1 — Domain — DONE

`modules/nutrition/domain/`:
- [x] `entities/diet_plan.py` — `DietPlan` aggregate root: `id`, `user_id`,
      `goal`, `diet_type`, `duration_days`, `requirements` (`tuple[str, ...]`,
      optional free-text hints), `days` (`tuple[DietDay, ...]`), `created_at`.
      `create()` validates `duration_days` is in a sane bounded range
      (1–14) and `days` actually has `duration_days` entries — same
      create()-time validation pattern as `NutritionProfile`.
- [x] `value_objects/diet_day.py` — `DietDay`: `day_number` (1-indexed),
      `meals` (`tuple[Meal, ...]`).
- [x] `value_objects/meal.py` — `Meal`: `name`, `calories`, `protein`,
      `carbohydrates`, `fat` (all non-negative numbers, enforced in
      `DietPlan.create()`).
- [x] `exceptions/diet_plan_domain_errors.py` — `InvalidDietPlanError`
      (subclasses the existing `NutritionDomainError`), covering bad
      `duration_days`, day-count mismatch, and negative macros.
- [x] `repositories/diet_plan_repository.py` — port: `get_by_id(plan_id) ->
      DietPlan | None`, `list_by_user_id(user_id) -> list[DietPlan]`,
      `save(plan) -> None`. Unlike `NutritionProfile`, a user can have many
      diet plans — no unique-per-user constraint, no `update()` method (a
      plan is generated fresh each time, not edited in place).

`modules/ai/domain/`:
- [x] `ports/llm_provider.py` — added
      `generate_structured_response(self, prompt: Prompt, schema: dict) ->
      dict` to `LLMProvider`. **Deviation from the original draft**: made it
      a concrete method with a `NotImplementedError` default body rather
      than `@abstractmethod` — an `@abstractmethod` would have broken
      instantiation of every existing provider (`MockLLMProvider`,
      `ClaudeProvider`, `OllamaProvider`, `FakeLLMProvider`) before Stage 3
      implements it there, which would have left the full suite red for two
      stages. This is an intentional "optional capability" port method, the
      same shape Python's `ABC` uses for mixin-style default behavior —
      Stage 3 overrides it in each real provider.

Exit criteria: unit tests for `DietPlan`/`DietDay`/`Meal` validation rules,
zero infra deps. 7 tests added (`test_diet_plan_entity.py`), full suite at
151/151 passing.

---

## Stage 2 — Application — DONE

`modules/nutrition/application/`:
- [x] `dto/diet_plan_dto.py` — `GenerateDietPlanCommand` (`user_id`,
      `duration_days`, `requirements: tuple[str, ...] | None`),
      `ListDietPlansQuery`, `GetDietPlanQuery`, `MealResult`/`DietDayResult`/
      `DietPlanResult`/`DietPlanSummaryResult` (`from_domain()` classmethods,
      mirroring `NutritionProfileResult`).
- [x] `use_cases/generate_diet_plan_use_case.py` — looks up the caller's
      `NutritionProfile` and **reuses the existing
      `NutritionProfileNotFoundError`** when it's missing (deliberate reuse,
      not a new error type — "you need a profile before generating a plan"
      is the same shape as "you need a profile before chatting gets
      personalized", and it already maps to 404 at the API layer). Builds a
      structured prompt via the new `DietPlanPromptBuilder` (in
      `ai/application/`), calls `LLMProvider.generate_structured_response`,
      maps the returned dict into `DietPlan.create(...)`, saves, returns
      `DietPlanResult`.
- [x] `use_cases/list_diet_plans_use_case.py`, `get_diet_plan_use_case.py` —
      new `DietPlanNotFoundError` for the get-by-id case (ownership check —
      404 for another user's plan, same don't-leak-existence shape as
      Conversation/Nutrition).
- [x] `ai/application/diet_plan_prompt_builder.py` — `DietPlanPromptBuilder`:
      `build()` composes the question + a dietitian-framed system prompt;
      `build_schema()` returns the JSON schema passed to
      `generate_structured_response`. **Deliberately no `minItems`/`maxItems`
      on the `days` array** — Claude's structured-output schema support
      excludes complex array constraints, so the exact day count is
      enforced by `DietPlan.create()` after parsing instead.
- [x] `tests/fakes.py` — `InMemoryDietPlanRepository`; extended
      `ai/tests/fakes.py`'s `FakeLLMProvider` with
      `generate_structured_response` (takes an explicit
      `canned_structured_response` dict per test, captures `last_prompt` +
      `last_schema`).

Exit criteria: use case tests pass against fakes only, no real DB/HTTP —
including a test that no-profile raises before ever calling the LLM
(`test_generate_diet_plan_without_profile_raises`). 12 tests added
(`test_generate_diet_plan_use_case.py`, `test_diet_plan_query_use_cases.py`),
full suite at 159/159 passing.

---

## Stage 3 — AI provider extension (real structured output) — DONE

- [x] `ai/infrastructure/anthropic/claude_provider.py` —
      `generate_structured_response` using `output_config: {"format":
      {"type": "json_schema", "schema": schema}}` on `messages.create()`,
      parses the guaranteed-valid JSON text block. Not exercised against the
      real Claude API in this environment (no `ANTHROPIC_API_KEY`
      configured in dev) — verified structurally via fakes (correct
      `output_config` shape, correct JSON parsing), same level of
      verification the original `ClaudeProvider.generate_response` got.
- [x] `ai/infrastructure/ollama/ollama_provider.py` —
      `generate_structured_response` sends `"format": "json"` in the
      `/api/chat` request body, `json.loads()`s the response, validates
      against a Pydantic model built from the schema (new
      `ollama/schema_validation.py`: converts the JSON-Schema subset our own
      prompt builders emit — object/array/string/integer/number/boolean,
      `required`, `additionalProperties` — into a dynamic Pydantic model via
      `create_model`). On a validation failure, retries **once** with the
      validation error appended to the prompt, then raises a `RuntimeError`
      if the retry also fails (fail loud — no silent fallback to a
      malformed plan, matching the project's existing `AI_PROVIDER`
      misconfiguration philosophy).
- [x] `ai/infrastructure/providers/mock_llm_provider.py` —
      `generate_structured_response` parses the requested day count out of
      `Prompt.question` (`DietPlanPromptBuilder` always writes "Generate a
      N-day diet plan…") and returns exactly `N` canned days — otherwise the
      mock provider would fail `DietPlan.create()`'s day-count validation
      for any `duration_days != 1`, making it useless for manual end-to-end
      testing of the Stage 5 API.
- [x] **Real-model finding, fixed during Stage 3 verification**: the
      original design (dump the raw JSON Schema into the prompt as
      instruction text) made `llama3.2:1b` echo the schema's own
      `type`/`properties` keys back as if they were the answer, and
      separately — once that was fixed — made it invent extra top-level
      keys per day (e.g. `"snacks"`, `"high_protein_breakfasts"`) by copying
      words from free-text `requirements` into new JSON keys instead of
      putting that content inside the existing `meals` list. Root cause:
      raw JSON Schema syntax and schema-shaped instructions are unreliable
      for very small local models. Fixed by adding
      `build_example_from_schema()` (renders a filled-in *example instance*
      instead of the schema definition — tiny models follow a concrete
      example far more reliably) plus an explicit instruction that
      requirements affect *content*, never *key names*. Verified empirically
      against the real Docker Ollama container across four separate runs
      (1-day, 2-day, 3-day-with-requirements, retry-triggering case) — all
      now produce schema-conformant JSON on the first or second attempt.

Exit criteria: provider-level tests (`test_claude_provider.py` — JSON-mode
request shape; `test_ollama_provider.py` — parse/validate,
retry-once-then-succeed, retry-once-then-raise; `test_mock_llm_provider.py`
— day-count matching) added, 6 tests, full suite at 165/165 passing.
Real-Ollama verification as described above (not just fakes) — Claude
verification deferred to whenever a real `ANTHROPIC_API_KEY` is available in
this environment, same caveat as every prior Claude-provider stage.

---

## Stage 4 — Infrastructure: Mongo persistence (Beanie) — DONE

- [x] `infrastructure/documents/diet_plan_document.py` — Beanie `Document`,
      `Settings.name = "diet_plans"`, index on `user_id` (not unique — many
      plans per user, unlike `NutritionProfileDocument`'s unique index).
      `days`/`meals` are embedded Pydantic models (`DietDayEmbed`,
      `MealEmbed`), not separate Beanie documents — they only ever exist
      nested inside a plan, same reasoning as `Message` living inline on
      `ConversationDocument` rather than its own collection.
- [x] `infrastructure/mappers/diet_plan_mapper.py` — Document ↔ domain.
      `to_document()` uses `dataclasses.asdict(day)` to flatten each
      `DietDay`/`Meal` dataclass into the nested dict shape
      `DietDayEmbed(**...)` expects — `asdict()` works with `slots=True`
      dataclasses (it introspects `fields()`, not `__dict__`).
- [x] `infrastructure/repository/mongo_diet_plan_repository.py` —
      `list_by_user_id` sorts by `-DietPlanDocument.created_at` (newest
      first, matching the port's documented contract).
- [x] Registered `DietPlanDocument` in `main.py`'s
      `init_beanie_documents([ConversationDocument, NutritionProfileDocument,
      DietPlanDocument])`.

Exit criteria: repository-level tests against the real ephemeral Mongo test
stack (save/get round-trip, unknown-id → `None`, list-by-user newest-first,
list-for-user-with-no-plans → `[]`), same isolation pattern as
`NutritionProfileDocument`'s Stage 3. 4 tests added, full suite at 169/169
passing. Also verified directly against the real dev Mongo (not just the
ephemeral test stack): saved and re-fetched a plan through the actual
running container's `MongoDietPlanRepository`.

---

## Stage 5 — API layer — DONE

Endpoints (per docs/api.md, updated to snake_case):

```
POST /diet-plans/generate
GET  /diet-plans
GET  /diet-plans/{diet_plan_id}
```

- [x] `api/schemas/diet_plan_schemas.py` — `GenerateDietPlanRequest`
      (`duration_days: int = Field(ge=1, le=14)`, `requirements:
      list[str] | None`), `MealResponse`/`DietDayResponse`/
      `DietPlanResponse`/`DietPlanSummaryResponse` (`from_result()`
      classmethods).
- [x] `api/dependencies/diet_plan_dependencies.py` — wires
      `NutritionProfileRepository` (reusing
      `nutrition_dependencies.get_nutrition_profile_repository`) +
      `DietPlanRepository` + `LLMProvider` into `GenerateDietPlanUseCase`,
      mirroring `SendMessageUseCase`'s cross-module DI shape from Phase 5/6
      Stage 5.
- [x] `api/routers/diet_plan_router.py` — `POST` → `AppException(NOT_FOUND)`
      if the caller has no nutrition profile yet (reusing
      `NutritionProfileNotFoundError`/`NOT_FOUND`, per Stage 2's decision —
      no new `ErrorCode` needed); `GET /diet-plans/{id}` →
      `AppException(NOT_FOUND)` for a nonexistent or non-owned plan.
      **No explicit handling needed for a malformed AI response**
      (`InvalidDietPlanError` from a day-count mismatch, or the `RuntimeError`
      from Ollama's failed retry) — both fall through to the existing
      generic `Exception` handler → `500 INTERNAL_ERROR`, consistent with
      the project's fail-loud philosophy for AI upstream failures.
- [x] Registered `diet_plan_router` in `nutrition/api/router.py` alongside
      `profile_router`.

Exit criteria: full API integration tests (generate-without-profile 404 →
generate 201 → requires-auth 401 → invalid-duration 422 → list-only-own →
get-full-plan → get-unknown-404 → get-other-users-plan-404), same shape as
`test_nutrition_api.py`. 8 tests added, full suite at 177/177 passing.
Verified end-to-end on the real Docker stack with Ollama: generated a real
2-day vegan/weight-loss plan through the full HTTP stack (~42s, realistic
meals, exactly 2 days), confirmed via `GET /diet-plans` (summary) and
`GET /diet-plans/{id}` (full plan, 200), and confirmed a nonexistent id
still 404s.

---

## Stage 6 — Tests & docs sync — DONE

- [x] `docs/https/diet-plan.http` — register → login → generate-without-profile
      404 → create profile → generate (2 days, no requirements) → generate
      with `requirements` (marked flaky on Ollama, see finding below) → list →
      get by id → no-token 401 → invalid-duration 422 → get-unknown-id 404 →
      second-user isolation (404 on the first user's plan, empty list). All
      steps replayed manually against the real Docker stack.
- [x] `docs/api.md` Diet Plan API section rewritten to the shipped
      snake_case shape — real request/response fields (`goal`/`diet_type`
      come from the profile, not the request), all three endpoints
      documented (the original draft only had two), and real error codes
      including the 500 case for a malformed AI response.
- [x] `architecture.md` — Nutrition Module section: `DietPlan`/`DietDay`/
      `Meal` marked implemented (were "future"); added a description of the
      generate flow and its profile-required 404. New **AI Module**
      subsection "Structured output" documenting `generate_structured_response`
      and how each provider (Claude/Ollama/Mock) implements it, including the
      real-model prompting finding from Stage 3.
- [x] `domain-model.md` — `DietPlan`/`DietDay`/`Meal` sections rewritten:
      real field names (`duration_days`, `day_number`, not the original
      draft's `duration`/`date`), `DietDay`/`Meal` reclassified from "Entity"
      to "Value Object" (they're embedded, no identity of their own —
      matches how they're actually modeled), dropped the never-implemented
      `description`/`ingredients`/`Ingredient` fields from the original
      sparse draft.
- [x] **Reliability finding from re-testing `diet-plan.http` against real
      Ollama**: even after Stage 3's prompt fix, `llama3.2:1b` can still
      invent extra keys (e.g. `"snacks_and_refills"`) and exhaust the
      retry-once, especially when free-text `requirements` are present —
      reproduced this on both a 2-day and 3-day plan with requirements
      (500), while the identical request *without* requirements succeeded
      reliably (201, ~31s). This isn't a new bug: it's the documented,
      accepted "fail loud" behavior for a 1B-parameter local model doing
      structured generation (Stage 3's `RuntimeError` design existed
      specifically for this case) — but it was real news that even the
      improved prompt doesn't make it fully reliable with `requirements`
      set. Documented in `architecture.md`, `api.md`, and `diet-plan.http`
      itself so nobody mistakes an occasional 500 here for a regression;
      not chased further since Claude's native structured output already
      solves this for anyone using `AI_PROVIDER=claude`.
- [x] **`README.md` — full rewrite**, not just a status-table touch-up: the
      previous version was the original pre-implementation planning draft
      (OpenAI instead of Claude/Ollama, Motor instead of Beanie's native
      PyMongo client, Python 3.13 instead of 3.12, a status table showing
      everything "⏳ in progress" despite Phases 3-7 being done, broken
      `docs/` references to files that were never created). Added a
      prominent **Getting Started** section up front covering: prerequisites,
      the exact `docker compose up -d --build` quick-start with a
      service/port table, what happens automatically on first boot (Ollama
      model pull, Alembic migrations), how to verify it's running, how to
      exercise the full flow via `docs/https/*.http`, how AI provider
      selection actually works (and its real limitation — `docker-compose.yml`
      sets env vars as literals with no `.env`/`${VAR}` substitution wired
      up, so switching providers under Docker means editing the compose
      file directly, not just copying `.env.example`), running without
      Docker, and running the test suite. **Every command in this section
      was actually run during this stage, not just written from reading the
      code** — this caught a real inaccuracy: Alembic reads `DATABASE_URL`
      (a sync `psycopg2` URL), not the app's own `POSTGRES_URL` (async
      `asyncpg`, used by `.env`) — a first draft of the local-dev
      instructions silently pointed at the wrong hostname
      (`alembic.ini`'s built-in default is the Docker service name `db`)
      and would have failed for anyone following it outside Docker.
- [x] Roadmap status table updated (this file).

Exit criteria: full suite still green after the docs-only changes
(177/177 — this stage touched no application code). `diet-plan.http`,
local-dev `uvicorn`, and the local `alembic` command from the new README
were each executed for real against this repo, not just written from
inspection.

---

# Phase 8 - Conversation Lifecycle & Account Recovery

Goal:

Before starting the frontend, close the most important user-facing gaps
found in a post-Phase-7 audit of the existing API: no `DELETE` endpoint
exists anywhere in the app, conversations can be archived in the domain
(`Conversation.archive()`, `ConversationStatus.ARCHIVED`) but there's no
route to reach it, and there is no password-recovery path at all — a user
who forgets their password is permanently locked out. Building a frontend
against an API with these gaps would mean redoing frontend calls later, so
this phase closes them first.

Scope, per user decision:
- **Conversation delete + archive** — `DELETE /conversations/{id}` (hard
  delete) and an endpoint to reach the existing `archive()` domain method.
- **Password reset** — with **real SMTP email delivery** (not a token
  returned in the response, and not just logged) — a **Mailhog** container
  is added to the dev stack so reset emails are genuinely sent and
  inspectable via its web UI, without needing real SMTP credentials.

Modules touched: `conversation` (new endpoints on an existing aggregate) and
`identity` (new `PasswordResetToken` aggregate + a new cross-cutting email
capability).

---

## Stage 1 — Conversation delete + archive (all layers) — DONE

Small enough to do as one stage — no new aggregate, `Conversation.archive()`
already existed in the domain (Phase 5/6 Stage 1); this only added the
missing routes and a repository-level delete.

`modules/conversation/`:
- [x] `domain/repositories/conversation_repository.py` — added
      `delete(conversation_id) -> None` to the `ConversationRepository` port.
- [x] `application/use_cases/archive_conversation_use_case.py` — loads by id,
      ownership check (`ConversationNotFoundError` for missing/non-owned,
      same don't-leak-existence shape as every other use case in this repo),
      calls `conversation.archive()`, saves, returns the updated
      conversation (reuses `GetConversationHistoryResult`'s shape rather
      than a near-duplicate DTO).
- [x] `application/use_cases/delete_conversation_use_case.py` — same
      ownership check, then `repository.delete(id)`.
- [x] `infrastructure/repository/mongo_conversation_repository.py` — added
      `delete()` (fetch by id, `.delete()` on the document if found).
- [x] `api/routers/conversation_router.py` —
      `POST /conversations/{conversation_id}/archive` (200, returns the
      updated conversation) and `DELETE /conversations/{conversation_id}`
      (204 No Content). Both 404 for missing/non-owned.
- [x] `tests/fakes.py` — `InMemoryConversationRepository.delete()`.

**Real bug found and fixed while testing this stage**: `SendMessageUseCase`
already raised `ArchivedConversationError` when messaging an archived
conversation (domain rule from Phase 5/6), but `conversation_router.py`'s
`send_message` endpoint only ever caught `ConversationNotFoundError` — the
archived-conversation path had no route to actually reach it until *this*
stage added the archive endpoint, so the gap was invisible until now. An
archived conversation's message attempt was falling through to the generic
`Exception` handler as an unintended 500. Fixed by catching
`ArchivedConversationError` → `409 Conflict` (`ErrorCode.CONFLICT`) — a
proper "action not allowed in the resource's current state" response
instead of an internal-error leak. Caught by the new
`test_archived_conversation_rejects_new_messages_via_api` test failing
against a real 500 before the fix.

Exit criteria: unit tests (fakes) for both use cases (including
already-archived / sending a message to an archived conversation still
raises `ArchivedConversationError` at the use-case layer, and now maps to
409 at the API layer — see the bug above), API integration tests (archive
→ verify status → delete → verify 404 on subsequent get, ownership checks
for both endpoints), Mongo repository-level delete tests against the real
ephemeral test stack. 16 tests added, full suite at 193/193 passing.
Verified end-to-end against the real Docker stack: create → archive
(200, status `ARCHIVED`) → send message (409) → delete (204) → get (404).

---

## Stage 2 — Password reset: domain + application — DONE

`modules/identity/domain/`:
- [x] `entities/password_reset_token.py` — `PasswordResetToken`: `id`,
      `user_id`, `token_hash`, `expires_at`, `used` (bool), `created_at`.
      Mirrors `RefreshToken`'s shape, but **the token is actually hashed at
      rest this time** (`hashlib.sha256`) — the existing `RefreshToken`
      stores the raw JWT in `token_hash` (a known, documented simplification
      in `refresh_access_token_use_case.py`); a reset token is short-lived
      and single-use but still a bearer credential mailed in plaintext, so
      hashing it at rest is the correct default for new code, not an
      inconsistency to "match" the older shortcut.
      `issue(user_id, ttl_minutes=30)` is a classmethod returning
      `(token, raw_token)` — the raw secret (`secrets.token_urlsafe(32)`)
      exists only transiently to be emailed; only its SHA-256 hash is ever
      persisted. Also: `hash_token()` (static), `is_expired()`,
      `is_valid()` (`not used and not is_expired()`), `mark_used()`.
- [x] `InvalidPasswordResetTokenError` — added to the existing
      `identity_domain_errors.py` (this module keeps all domain errors in
      one file already, unlike nutrition's per-aggregate split — followed
      identity's own convention rather than nutrition's).
- [x] `repositories/password_reset_token_repository.py` — port:
      `save(token)`, `get_by_token_hash(hash) -> PasswordResetToken | None`.
- [x] `User.change_password(new_password_hash)` + new `PasswordChanged`
      domain event — added to keep password mutation encapsulated in the
      entity (matching `deactivate()`/`block()`/`activate()`'s shape)
      rather than the use case reaching in and setting
      `user.password_hash` directly.
- [x] `RefreshTokenRepository.revoke_all_for_user(user_id)` — added as a
      **concrete method with a `NotImplementedError` default**, not
      `@abstractmethod` — same reasoning as `LLMProvider.
      generate_structured_response` in Phase 7 Stage 1: an `@abstractmethod`
      would have broken the existing `SqlAlchemyRefreshTokenRepository`'s
      instantiation (used by every register/login/refresh request) before
      Stage 3 implements it for real. `InMemoryRefreshTokenRepository`
      (fake) got a real implementation now since `ConfirmPasswordResetUseCase`'s
      own tests need to exercise it.

`modules/identity/application/`:
- [x] `ports/email_sender.py` — `EmailSender` ABC: `async send(self, to:
      str, subject: str, body: str) -> None`. Placed alongside the existing
      `ports/token_service.py` (identity-scoped port; promote to `shared/`
      later if a second module needs it — YAGNI over speculative reuse).
- [x] `use_cases/request_password_reset_use_case.py` — looks up the user by
      email; **always returns success regardless of whether the email
      exists or is even well-formed** (same don't-leak-existence principle
      as login/refresh error handling, extended to email enumeration and to
      malformed-email input) — if found, issues a `PasswordResetToken`
      (30-minute expiry), saves it, and sends an email via `EmailSender`
      containing the raw token. If not found (or malformed), does nothing.
- [x] `use_cases/confirm_password_reset_use_case.py` — hashes the incoming
      token, looks it up, validates `is_valid()` (raises
      `InvalidPasswordResetTokenError`, intended to map to 400 at the API
      layer in Stage 4 — not 404, so as not to leak whether *some* token
      exists vs this one being expired/used), re-validates the new password
      via the existing `PasswordPolicy`, calls `user.change_password(...)`,
      marks the token used, and **revokes all of the user's active refresh
      tokens** via the new `revoke_all_for_user`.
- [x] `tests/fakes.py` — `InMemoryPasswordResetTokenRepository`,
      `FakeEmailSender` (captures sent emails — `to`/`subject`/`body` — in a
      `sent` list for assertions, same shape as `FakeLLMProvider` capturing
      `last_prompt`), `InMemoryRefreshTokenRepository.revoke_all_for_user`.

Exit criteria: use case tests against fakes only — 17 tests added across
`test_password_reset_token.py` (entity rules), `test_user_entity.py`
(`change_password` addition), `test_request_password_reset_use_case.py`
(unknown/malformed email → no email sent, known email → exactly one email
with a valid token), `test_confirm_password_reset_use_case.py`
(valid-token success + password changed + refresh tokens revoked,
unknown/expired/already-used token → raises, weak new password → raises).
Full suite at 210/210 passing.

---

## Stage 3 — Password reset: infrastructure (Postgres + email)

`modules/identity/infrastructure/`:
- [ ] `persistence/models/password_reset_token_model.py` — SQLAlchemy model,
      `password_reset_tokens` table, index on `token_hash` (unique) and
      `user_id`.
- [ ] Alembic migration — new table.
- [ ] `persistence/sqlalchemy_password_reset_token_repository.py`.
- [ ] `persistence/sqlalchemy_refresh_token_repository.py` — add
      `revoke_all_for_user(user_id)`.
- [ ] `infrastructure/email/smtp_email_sender.py` — `SmtpEmailSender` using
      `aiosmtplib` (async, matches the rest of the codebase's async I/O;
      no heavier framework like `fastapi-mail` needed for a single
      plain-text send).
- [ ] `infrastructure/email/mock_email_sender.py` — `MockEmailSender`,
      captures sent emails in memory; used when `EMAIL_PROVIDER=mock`
      (the default — mirrors `AI_PROVIDER`'s mock-by-default design so the
      test suite and quick local runs never need a real SMTP server).
- [ ] `infrastructure/email/email_sender_factory.py` —
      `build_email_sender(settings)` / `init_email_sender` /
      `close_email_sender` / `get_email_sender`, same singleton-lifecycle
      shape as `ai/infrastructure/provider_factory.py`; wired into
      `main.py`'s lifespan.
- [ ] `shared/config/settings.py` — `email_provider: str = "mock"`,
      `smtp_host`, `smtp_port`, `smtp_from_address`.
- [ ] `docker-compose.yml` — new `mailhog` service (SMTP catcher +
      web UI, no real credentials needed); `backend` gets
      `EMAIL_PROVIDER=smtp`, `SMTP_HOST=mailhog`, `SMTP_PORT=1025`,
      `SMTP_FROM_ADDRESS=noreply@dietai.local`, and depends on `mailhog`.
- [ ] `requirements.txt` — add `aiosmtplib`.

Exit criteria: repository tests against the real ephemeral Postgres test
stack (save/get round-trip, hash lookup, `revoke_all_for_user`); verified
end-to-end against the real dev stack: sent a real email through
`SmtpEmailSender` → `mailhog` and confirmed it via Mailhog's HTTP API
(`GET http://localhost:8025/api/v2/messages`).

---

## Stage 4 — Password reset: API

Endpoints (per docs/api.md, snake_case):

```
POST /auth/password-reset/request
POST /auth/password-reset/confirm
```

- [ ] `api/schemas/password_reset_schemas.py` — `RequestPasswordResetRequest`
      (`email`), `ConfirmPasswordResetRequest` (`token`, `new_password` —
      same strength validation as registration).
- [ ] `api/dependencies/password_reset_dependencies.py` — wires
      `PasswordResetTokenRepository` + `UserRepository` + `EmailSender` into
      `RequestPasswordResetUseCase`; `PasswordResetTokenRepository` +
      `UserRepository` + `RefreshTokenRepository` into
      `ConfirmPasswordResetUseCase`.
- [ ] `api/routers/auth_router.py` — both endpoints always return `200`
      with a generic body on `request` (never reveals whether the email
      exists); `confirm` → `AppException(BAD_REQUEST)` (or a dedicated
      `ErrorCode` if the review decides it's worth one) on
      `InvalidPasswordResetTokenError`.

Exit criteria: full API integration tests (request-unknown-email 200 +
no email sent; request-known-email 200 + exactly one email sent via
`FakeEmailSender`/`MockEmailSender`; confirm-valid-token 200 + old
password no longer works + old refresh token revoked; confirm-expired/
used/garbage-token → 400). Verified end-to-end on the real Docker stack:
request → fetch the email from Mailhog's API → extract the token →
confirm → log in with the new password.

---

## Stage 5 — Tests & docs sync

- [ ] `docs/https/user.http` — add archive/delete steps for conversations
      (or extend `conversation.http`) and a new password-reset flow
      section (request → read token from Mailhog manually → confirm →
      login with new password).
- [ ] `docs/api.md` — new endpoints documented (Conversation archive/delete,
      both password-reset endpoints).
- [ ] `docs/architecture.md` — note the new `PasswordResetToken` aggregate,
      the `EmailSender` port/Mailhog addition, and the
      `revoke-all-refresh-tokens-on-reset` behavior.
- [ ] `docs/domain-model.md` — `PasswordResetToken` entity documented.
- [ ] `docs/auth-runbook.md` — extended with the password-reset flow.
- [ ] `README.md` — mention the `mailhog` service and its web UI
      (http://localhost:8025) in the Getting Started service table.
- [ ] Roadmap status table updated.

---

# Phase 9 - Frontend

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

# Phase 10 - Testing

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

# Phase 11 - Future Improvements

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
- [x] User can start conversation
- [x] User can chat with AI
- [x] Conversation history is stored
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