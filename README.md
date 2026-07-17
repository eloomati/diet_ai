# Diet AI

> AI-powered nutrition assistant built with Python, FastAPI, Domain-Driven Design and Hexagonal Architecture.

---

# Overview

Diet AI is an AI-powered nutrition assistant that allows authenticated users to chat with a Large Language Model (LLM), maintain a nutrition profile, and generate personalized structured diet plans.

The application combines modern backend architecture with AI integration while following enterprise software engineering practices inspired by Java/Spring Boot development.

The project is primarily a learning platform focused on building production-quality software rather than simply creating a working application.

---

# Getting Started

The fastest way to run the whole stack is Docker Compose — it starts the API, PostgreSQL, MongoDB, and a local Ollama LLM container together, with migrations and model download handled automatically.

## Prerequisites

- **Docker** and **Docker Compose** (the only hard requirement for the path below)
- **Git**
- Optional, only needed if you want to run tests or develop outside Docker: **Python 3.12+** and **pip** (Docker must still be running in that case — see [Running the tests](#running-the-tests))

## 1. Clone the repository

```bash
git clone https://github.com/eloomati/diet_ai.git
cd diet_ai
```

## 2. Start the full stack

```bash
docker compose up -d --build
```

This builds the backend image and starts five containers:

| Service   | Container         | Port        | Purpose                                             |
|-----------|--------------------|-------------|------------------------------------------------------|
| `backend` | `diet_ai_backend`  | 8000        | FastAPI application                                  |
| `db`      | `diet_ai_db`       | 5432        | PostgreSQL — Identity module                         |
| `mongo`   | `diet_ai_mongo`    | 27017       | MongoDB — Conversation + Nutrition modules           |
| `ollama`  | `diet_ai_ollama`   | 11434       | Local LLM — powers chat + diet-plan generation by default |
| `mailhog` | `diet_ai_mailhog`  | 1025 / 8025 | Local SMTP catcher — password-reset/verification emails land here, not a real inbox. Web UI at http://localhost:8025 |

**First start takes a few minutes** — two things happen automatically, no action needed:

- the `ollama` container pulls the `llama3.2:1b` model (~1.3 GB) on first boot; watch progress with `docker compose logs -f ollama`
- the `backend` container waits for PostgreSQL, then runs Alembic migrations itself (`docker/entrypoint.sh`) before starting `uvicorn`

`backend` won't start until `db`, `mongo`, and `ollama` all report healthy. Check status with:

```bash
docker compose ps
```

## 3. Verify it's running

Open **http://localhost:8000/docs** for the interactive Swagger UI, or:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "StrongPass123"}'
```

## 4. Try the full flow

`docs/https/*.http` files (compatible with the VS Code **REST Client** extension or JetBrains' built-in HTTP client) walk through each module end-to-end with real requests:

| File | Covers |
|---|---|
| `docs/https/user.http` | register → login → refresh → logout → `/me`, plus email verification and password reset (reads the raw token straight out of Mailhog's API — no manual copy/paste) |
| `docs/https/conversation.http` | create a conversation → chat with the AI → view history → archive → delete |
| `docs/https/nutrition.http` | create/get/update a nutrition profile |
| `docs/https/diet-plan.http` | generate a structured multi-day diet plan (needs a nutrition profile first) |

The email-related steps in `user.http` need `EMAIL_PROVIDER=smtp` (the
`docker-compose.yml` default) so mail actually lands in Mailhog — see the
service table above.

Or use `curl`/Swagger directly — the full request/response contract is documented in `docs/api.md`.

## Configuring the AI provider

The default in `docker-compose.yml` is `AI_PROVIDER=ollama` — chat and diet-plan generation both go through the bundled local `llama3.2:1b` container, no API key required.

| `AI_PROVIDER` | Requires | Notes |
|---|---|---|
| `mock` | nothing | Deterministic canned responses, no network calls — fastest; what the test suite uses by default |
| `ollama` | nothing (bundled container) | Real local LLM, no external cost. Slower, and less reliable specifically for diet-plan structured output on such a small model — see `docs/architecture.md` § Structured output |
| `claude` | `ANTHROPIC_API_KEY` | Real Claude API — best quality, and the only option with a genuine structured-output guarantee for diet plans |

**Note:** `docker-compose.yml` sets these as literal environment values for the `backend` service — it does **not** read a `.env` file (no `env_file:`/`${VAR}` substitution is wired up). To switch providers under Docker, edit `docker-compose.yml`'s `backend.environment` block directly, e.g.:

```yaml
AI_PROVIDER: claude
ANTHROPIC_API_KEY: "sk-ant-your-key-here"
```

then re-apply with:

```bash
docker compose up -d --build backend
```

(`.env`/`.env.example` *is* read by the app when running locally without Docker — see below.)

## Running without Docker (local development)

Requires a local PostgreSQL and MongoDB (or reuse the Docker ones — see step 4).

```bash
# 1. Create and activate a virtualenv
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment — this file IS read locally (unlike Docker Compose above)
cp .env.example .env
# edit .env: at minimum set a real JWT_SECRET_KEY, and POSTGRES_URL/MONGO_URL
# if not using the defaults (localhost:5432 / localhost:27017)

# 4. Start just the databases via Docker if you don't have local ones
docker compose up -d db mongo

# 5. Run database migrations
# Note: Alembic reads DATABASE_URL (sync psycopg2 URL), NOT the app's own
# POSTGRES_URL (async asyncpg URL used by .env) — alembic.ini's built-in
# default even points at hostname "db" (the Docker service name), so this
# export is required when running outside Docker:
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/diet_ai"
alembic -c backend/alembic.ini upgrade head

# 6. Start the API with auto-reload
uvicorn backend.app.main:app --reload
```

The API is now live at http://localhost:8000 (Swagger at `/docs`), with `AI_PROVIDER=mock` by default (per `.env.example`) — switch to `ollama` or `claude` in `.env` the same way as above.

## Running the tests

```bash
pip install -r requirements.txt
pytest
```

- **Docker must be running.** A session-scoped, autouse `pytest` fixture (`conftest.py`) automatically spins up throwaway PostgreSQL + MongoDB containers via `docker-compose.test.yml` (ports `5433`/`27018` — fully isolated from the dev stack above) and tears them down when the run finishes.
- Defaults to `AI_PROVIDER=mock` (see `pytest.ini`) — the suite makes no real network/LLM calls and needs no API key.
- 177 tests as of Phase 7 (Diet Generation).

## Stopping / cleaning up

```bash
docker compose down       # stop containers, keep data (Postgres/Mongo/Ollama volumes persist)
docker compose down -v    # stop containers AND delete volumes — fresh start next time
```

---

# Project Goals

## Technical Goals

- Learn Python from a Java Backend perspective
- Learn FastAPI
- Learn Hexagonal Architecture
- Learn Domain Driven Design (DDD)
- Learn AI integration
- Learn Docker
- Learn MongoDB
- Learn PostgreSQL
- Learn Polyglot Persistence

---

## Business Goals

Allow users to:

- register and authenticate
- recover access via password reset and verify their email address
- manage a personal nutrition profile
- chat with AI for personalized nutrition advice
- generate personalized, structured multi-day diet plans
- browse, archive, and delete conversation history
- receive context-aware responses (chat and diet plans both use the user's nutrition profile)
- generate nutrition reports (future)

---

# Current Project Status

| Phase | Status |
|--------|--------|
| Documentation | ✅ |
| Architecture | ✅ |
| Domain Model | ✅ |
| Backend Bootstrap | ✅ |
| Identity (register/login/refresh/JWT) | ✅ |
| Nutrition Profile | ✅ |
| Conversation + AI chat | ✅ |
| Diet Plan Generation | ✅ |
| Conversation Lifecycle & Account Recovery (archive/delete, logout, password reset, email verification) | ✅ |
| Frontend | ⏳ |
| Reporting | ⏳ |

See `docs/implementation-roadmap.md` for the full stage-by-stage history of every phase.

---

# High Level Architecture

```text
                    React Frontend (future)
                           │
                           │
                     FastAPI Backend
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
 Identity Module   Conversation Module   Nutrition Module
      │                    │                    │
 PostgreSQL           MongoDB             MongoDB
                           │                    │
                           └─────────┬──────────┘
                                     │
                                AI Module
                                     │
                        Claude API / Ollama (local)
```

---

# Architectural Style

The application follows:

- Modular Monolith
- Domain Driven Design
- Hexagonal Architecture
- Rich Domain Model
- SOLID Principles
- Clean Architecture

Every business module is internally implemented using Hexagonal Architecture.

Modules are isolated and can be extracted into microservices in the future if required.

---

# Polyglot Persistence

The application intentionally uses two databases.

## PostgreSQL

Stores transactional and relational data.

Responsibilities:

- Users
- Authentication
- Refresh Tokens

ORM:

- SQLAlchemy 2.x (async, via `asyncpg`)

Migration Tool:

- Alembic

---

## MongoDB

Stores document-oriented data.

Responsibilities:

- Conversations and Messages
- Nutrition Profiles
- Diet Plans

ODM:

- Beanie, on top of PyMongo's native async client (`pymongo.AsyncMongoClient`) — **not** Motor, which MongoDB has deprecated in favor of PyMongo's own async API.

---

# Technology Stack

## Backend

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x + asyncpg
- Alembic
- Beanie ODM (on `pymongo.AsyncMongoClient`)
- PyJWT + bcrypt (authentication)

---

## Databases

- PostgreSQL
- MongoDB

---

## AI

- **Claude** (`anthropic` SDK) — primary cloud provider, default model `claude-opus-4-8`
- **Ollama** — bundled self-hosted local LLM (`llama3.2:1b`), no API key or external cost
- **Mock** — deterministic, network-free provider used by the test suite and for quick local iteration

Provider selection is a single `AI_PROVIDER` environment variable — see [Configuring the AI provider](#configuring-the-ai-provider) above.

---

## Frontend

Not started yet. Planned:

- React
- Vite
- Tailwind CSS

---

## Infrastructure

- Docker
- Docker Compose

Future:

- Kubernetes
- Redis
- Vector Database

---

# Project Structure

```text
diet_ai/
│
├── backend/              # FastAPI application (see below)
│
├── frontend/              # not started yet
│
├── docs/                  # architecture, domain model, API contract, roadmap, .http smoke tests
│
├── docker/                # entrypoint.sh (waits for Postgres, runs migrations, then execs uvicorn)
│
├── Dockerfile
├── docker-compose.yml       # dev stack: db, mongo, ollama, mailhog, backend
├── docker-compose.test.yml  # ephemeral test stack, auto-managed by conftest.py
├── conftest.py
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt      # -> requirements.txt (no separate dev/prod split)
├── .env.example
└── README.md
```

---

# Backend Structure

```text
backend/
│
├── app/            # FastAPI app factory, lifespan, top-level router
├── modules/        # one folder per business module (see below)
├── shared/         # cross-module infra: config, database clients, logging, exceptions, middleware, security, utils
├── tests/          # shared/root-level tests (e.g. error format)
├── alembic/        # PostgreSQL migrations
└── alembic.ini
```

---

# Modules

Every business capability is implemented as a separate module, each following Hexagonal Architecture.

```text
modules/
│
├── identity/       # registration, auth, JWT — PostgreSQL
├── conversation/    # AI chat, message history — MongoDB
├── nutrition/       # nutrition profile, diet plan generation — MongoDB
├── ai/              # LLM provider abstraction (Claude / Ollama / Mock)
└── reporting/       # future — statistics, exports
```

---

# Hexagonal Architecture

Every module contains the same internal structure:

```text
<module>/
│
├── api/            # routers, request/response schemas, DI wiring
├── application/     # use cases, DTOs
├── domain/          # entities, value objects, domain exceptions, repository ports
├── infrastructure/   # DB documents/models, mappers, repository implementations, external providers
└── tests/
```

---

# Layer Responsibilities

## API

Responsible for:

- REST endpoints
- Request/response validation (Pydantic schemas)
- Authentication (`get_current_user` dependency)
- Mapping application-layer results to HTTP responses/errors

Contains no business logic.

---

## Application

Responsible for:

- Use cases
- Orchestration between domain and infrastructure (repositories, AI providers)
- DTOs (commands/queries/results)

---

## Domain

Responsible for:

- Entities and Aggregate Roots
- Value Objects
- Business rules and validation
- Repository ports (abstract interfaces)
- Domain exceptions

The Domain never depends on FastAPI, SQLAlchemy, Beanie/MongoDB, or any AI SDK.

---

## Infrastructure

Responsible for:

- PostgreSQL (SQLAlchemy models, repository implementations)
- MongoDB (Beanie documents, repository implementations)
- AI providers (Claude, Ollama, Mock)
- Security (JWT, password hashing)

Infrastructure implements the ports defined in Domain.

---

# Main Modules

## Identity

Responsible for:

- registration, login, JWT access + refresh tokens (with reuse detection)
- current-user resolution (`GET /me`)

Database: PostgreSQL

---

## Conversation

Responsible for:

- creating conversations (with a category, e.g. `BREAKFAST`, `GYM`, `DIET`)
- sending messages and getting an AI response, personalized by the user's nutrition profile when one exists
- conversation history

Database: MongoDB

---

## Nutrition

Responsible for:

- nutrition profile CRUD (age, height, weight, activity level, goal, diet type)
- AI-generated structured multi-day diet plans, seeded from the user's nutrition profile plus optional free-text requirements

Database: MongoDB

---

## AI

Responsible for:

- `LLMProvider` abstraction — free-text (`generate_response`) and structured-JSON
  (`generate_structured_response`) generation
- Prompt building (`PromptBuilder` for chat, `DietPlanPromptBuilder` for diet plans)

Stateless module — no persistence of its own.

---

## Reporting

Future module.

Responsible for:

- statistics
- exports
- reports

---

# AI Architecture

The application never talks to Claude or Ollama directly from business code — it goes through an abstraction:

```text
LLMProvider (port)
       │
       ├── ClaudeProvider   — official `anthropic` SDK
       ├── OllamaProvider   — raw HTTP (no official SDK exists)
       └── MockLLMProvider  — deterministic, no network calls
```

Selection happens purely via the `AI_PROVIDER` setting — the rest of the application is unaware of which provider is active. See `docs/architecture.md` § AI Module for how each provider implements structured output (used by diet-plan generation).

---

# Authentication

Authentication uses:

- JWT Access Token (short-lived)
- Refresh Token (longer-lived, rotated on use, reuse detection invalidates the whole family)

Every endpoint except `/auth/register` and `/auth/login` requires a valid JWT.

---

# Development Principles

- Domain Driven Design
- Hexagonal Architecture
- Rich Domain Model
- SOLID
- Clean Code
- Feature-first organization
- Technology independence

---

# Documentation

Project documentation lives in `docs/`:

| File | Contents |
|---|---|
| `docs/architecture.md` | Module boundaries, persistence choices, AI provider architecture |
| `docs/domain-model.md` | Bounded contexts, aggregates, entities, value objects, domain rules |
| `docs/api.md` | Full REST API contract (all modules) |
| `docs/auth-runbook.md` | Auth error format + manual verification runbook |
| `docs/implementation-roadmap.md` | Stage-by-stage build history for every phase, including verification notes |
| `docs/https/*.http` | Runnable end-to-end request walkthroughs per module (see [Getting Started](#4-try-the-full-flow)) |

---

# Future Improvements

- Shopping Lists
- PDF Export
- Email Notifications
- Semantic Search
- AI Memory
- Background Workers
- Mobile Application
- Vector Database
- Frontend (React/Vite/Tailwind)
- Reporting module

---

# Learning Objectives

This project is intentionally designed to resemble an enterprise backend system.

The focus is on understanding software architecture, domain modeling and clean application design rather than simply implementing features.

---

# Author

Mateusz Hetko
