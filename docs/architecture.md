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

              OpenAI Provider / Local Model
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

- Beanie ODM

Main entities:

```
Conversation

Message
```

---

# Nutrition Module

Responsible for nutrition-related business logic.

Responsibilities:

- nutrition profile,
- user goals,
- diet generation,
- meal recommendations.

Database:

MongoDB

Main entities:

```
NutritionProfile

DietPlan

Meal
```

---

# AI Module

Responsible for communication with AI models.

The module provides an abstraction over AI providers.

Example:

```
LLMProvider

        |

        |

+----------------+

| OpenAIProvider |

| OllamaProvider |

+----------------+
```

The rest of the application does not know which AI provider is used.

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