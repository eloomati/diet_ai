# Diet AI - Implementation Roadmap

## Purpose

This document defines the implementation order of the Diet AI project.

The goal is to build the system incrementally while keeping architecture clean.

Each phase should result in a working part of the system.

---

# Phase 0 - Project Bootstrap

Goal:

Create a working development environment.

## Tasks

### Repository

- [ ] Create monorepo structure
- [ ] Initialize Git repository
- [ ] Create README
- [ ] Create documentation structure

---

### Backend

- [ ] Create Python project
- [ ] Configure dependency management
- [ ] Create FastAPI application
- [ ] Configure application settings
- [ ] Add environment variables support

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

- [ ] Backend container
- [ ] PostgreSQL container
- [ ] MongoDB container

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

- [ ] Configuration management
- [ ] Dependency injection
- [ ] Exception handling
- [ ] Logging basics

---

# Phase 2 - Database Setup

Goal:

Prepare persistence layer.

---

# PostgreSQL

Used by Identity.

Tasks:

- [ ] Configure SQLAlchemy
- [ ] Configure database connection
- [ ] Configure Alembic
- [ ] Create first migration

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

- [ ] User entity
- [ ] Password hashing
- [ ] User validation rules

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

- [ ] SQLAlchemy models
- [ ] User repository
- [ ] JWT provider
- [ ] Password encoder

---

## API

Endpoints:

```
POST /auth/register

POST /auth/login

POST /auth/refresh
```

---

Expected result:

User can:

- create account,
- login,
- receive JWT token.

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

# Phase 5 - Conversation Module

Goal:

Implement chat history.

Database:

MongoDB

---

## Domain

Create:

```
Conversation

Message
```

---

## Application

Create:

```
CreateConversationUseCase

SendMessageUseCase

GetConversationHistoryUseCase
```

---

## Infrastructure

Implement:

- [ ] Beanie documents
- [ ] Mongo repository

---

## API

Endpoints:

```
POST /conversations

GET /conversations

GET /conversations/{id}

POST /conversations/{id}/messages
```

---

Expected result:

User can:

- create conversation,
- send messages,
- see history.

---

# Phase 6 - AI Integration

Goal:

Connect conversation flow with AI.

---

## Domain

Create abstraction:

```
LLMProvider
```

---

## Infrastructure

Implement:

First:

```
FakeLLMProvider
```

Example:

```
"AI response example"
```

---

Then:

```
OpenAIProvider
```

---

Application flow:

```
User message

↓

Conversation

↓

Prompt Builder

↓

LLM Provider

↓

AI Response

↓

Save Message
```

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

- [ ] User can register
- [ ] User can login
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