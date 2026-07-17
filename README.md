# Diet AI

> AI-powered nutrition assistant built with Python, FastAPI, Domain-Driven Design and Hexagonal Architecture.

---

# Overview

Diet AI is an AI-powered nutrition assistant that allows authenticated users to chat with a Large Language Model (LLM) and receive personalized dietary recommendations.

The application combines modern backend architecture with AI integration while following enterprise software engineering practices inspired by Java/Spring Boot development.

The project is primarily a learning platform focused on building production-quality software rather than simply creating a working application.

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
- manage personal profile
- chat with AI
- generate personalized diet plans
- browse conversation history
- receive context-aware responses
- generate nutrition reports (future)

---

# Current Project Status

| Phase | Status |
|--------|--------|
| Documentation | ✅ |
| Architecture | ✅ |
| Domain Model | ✅ |
| Event Storming | ✅ |
| Command Model | ✅ |
| Backend Bootstrap | ⏳ |
| Authentication | ⏳ |
| AI Integration | ⏳ |
| Frontend | ⏳ |

---

# High Level Architecture

```text
                    React Frontend
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
      └──────────────┬─────┘
                     │
                AI Module
                     │
          OpenAI / Ollama
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
- Roles
- Permissions
- Sessions

ORM:

- SQLAlchemy 2.x

Migration Tool:

- Alembic

---

## MongoDB

Stores document-oriented data.

Responsibilities:

- Conversations
- Messages
- Diet Plans
- Reports

ODM:

- Beanie

---

# Technology Stack

## Backend

- Python 3.13
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- Beanie ODM
- Motor

---

## Databases

- PostgreSQL
- MongoDB

---

## AI

Initially:

- OpenAI API

Future:

- Ollama
- Gemma
- Mistral
- Phi

---

## Frontend

- React
- Vite
- Tailwind CSS

---

## Infrastructure

- Docker
- Docker Compose

Future:

- Kubernetes
- RabbitMQ (if needed)
- Redis
- Vector Database

---

# Project Structure

```text
diet-ai/
│
├── backend/
│
├── frontend/
│
├── docs/
│
├── docker/
│
├── scripts/
│
├── docker-compose.yml
│
└── README.md
```

---

# Backend Structure

```text
backend/

app/

modules/

shared/

tests/

alembic/

main.py
```

---

# Modules

Every business capability is implemented as a separate module.

```text
modules/

identity/

conversation/

nutrition/

ai/

reporting/
```

Each module follows Hexagonal Architecture.

---

# Hexagonal Architecture

Every module contains the same internal structure.

```text
identity/

api/

application/

domain/

infrastructure/

tests/
```

---

# Layer Responsibilities

## API

Responsible for:

- REST
- DTO validation
- Authentication
- Response mapping

Contains no business logic.

---

## Application

Responsible for:

- Use Cases
- Transaction boundaries
- Business orchestration

---

## Domain

Responsible for:

- Entities
- Value Objects
- Business Rules
- Aggregate Roots
- Domain Events

The Domain must never depend on FastAPI, SQLAlchemy, MongoDB or OpenAI.

---

## Infrastructure

Responsible for:

- PostgreSQL
- MongoDB
- AI Providers
- Security
- External Services

Infrastructure implements Domain Ports.

---

# Main Modules

## Identity

Responsible for:

- registration
- authentication
- authorization
- user management

Database:

PostgreSQL

---

## Conversation

Responsible for:

- chat
- conversation history
- messages

Database:

MongoDB

---

## Nutrition

Responsible for:

- nutrition profile
- diet generation
- recommendations

Database:

MongoDB

---

## AI

Responsible for:

- Prompt Builder
- LLM communication
- AI abstraction

Stateless module.

---

## Reporting

Future module.

Responsible for:

- statistics
- exports
- reports

---

# AI Architecture

The application never communicates directly with OpenAI.

Instead it uses an abstraction.

```text
LLM Provider

↓

OpenAI Provider

or

Ollama Provider
```

Changing the provider should require configuration only.

---

# Authentication

Authentication uses:

- JWT Access Token
- Refresh Token

Every endpoint except authentication requires a valid JWT.

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

Project documentation is located inside:

```text
docs/
```

Important documents:

```text
architecture/

architecture.md

domain-model.md

event-storming.md

command-model.md

hexagonal.md
```

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

---

# Learning Objectives

This project is intentionally designed to resemble an enterprise backend system.

The focus is on understanding software architecture, domain modeling and clean application design rather than simply implementing features.

---

# Author

Mateusz Hetko