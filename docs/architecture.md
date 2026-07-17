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

- registration,
- authentication,
- JWT handling,
- refresh tokens,
- user account management.

Database:

PostgreSQL

Technology:

- SQLAlchemy
- Alembic

Main entities:

```
User

RefreshToken
```

---

# Conversation Module

Responsible for AI conversations.

Responsibilities:

- creating conversations,
- storing messages,
- maintaining chat history,
- communication workflow with AI.

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
Conversation

Message
```

---

# Nutrition Module

Responsible for nutrition-related business logic.

Responsibilities:

- nutrition profile (implemented),
- user goals (implemented, part of the profile),
- diet generation (future — see `Phase 7+` in implementation-roadmap.md),
- meal recommendations (future).

Database:

MongoDB (Beanie, same client/setup as Conversation — see above).

Technology:

- Beanie ODM, `nutrition_profiles` collection with a unique index on
  `user_id` (one profile per user, enforced at the DB layer).

Main entities:

```
NutritionProfile   — implemented: age, height_cm, weight_kg, activity_level,
                     goal, diet_type

DietPlan           — future (Phase 7+)

Meal               — future (Phase 7+)
```

Status: `NutritionProfile` CRUD (`GET`/`POST`/`PUT /profile`) is implemented
and wired into the AI module — `SendMessageUseCase` looks up the caller's
profile and folds `NutritionProfile.as_prompt_text()` into the system prompt
via `PromptBuilder`, so chat responses are personalized when a profile
exists (chatting still works fine with no profile set).

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

Expected services:

```
backend

frontend

postgres

mongodb
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