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

createdAt

updatedAt
```

---

## User Rules

Business rules:

- email must be unique,
- password cannot be stored as plain text,
- inactive users cannot authenticate.

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

category

status

createdAt

updatedAt
```

---

## Conversation Rules

- Conversation belongs to one user.
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

Aggregate Root.

Represents user nutrition information.

This entity does NOT belong to Identity because it represents business information related to nutrition, not authentication.

Example:

```
NutritionProfile

id

userId

age

height

weight

activityLevel

goal

dietType
```

---

## NutritionProfile Rules

Examples:

- profile belongs to one user,
- weight and height must have valid values,
- goals define diet recommendations.

---

# DietGoal

Value Object.

Represents user's nutrition objective.

Examples:

```
WeightLoss

MuscleGain

Maintenance

Performance
```

---

# DietPlan

Aggregate Root.

Represents an AI-generated diet plan.

Example:

```
DietPlan

id

userId

goal

duration

createdAt

days
```

---

# DietDay

Entity.

Represents one day of a diet plan.

Example:

```
DietDay

date

meals
```

---

# Meal

Entity.

Represents a single meal.

Example:

```
Meal

name

description

calories

protein

carbohydrates

fat

ingredients
```

---

# Ingredient

Value Object.

Example:

```
Ingredient

name

amount

unit
```

Ingredient does not have its own identity.

---

# 7. AI Domain

The AI context provides abstraction over external AI systems.

---

# LLMProvider

Domain Port.

Example:

```
LLMProvider

generateResponse(prompt)
```

Possible implementations:

```
OpenAIProvider

OllamaProvider
```

---

# Prompt

Value Object.

Represents complete context sent to AI.

Example:

```
Prompt

systemContext

userProfile

conversationHistory

category

question
```

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

# 8. Aggregates

Current aggregate roots:

```
User

Conversation

NutritionProfile

DietPlan
```

Rules:

- aggregate roots control their internal state,
- external objects cannot modify aggregate internals directly.

---

# 9. Domain Events

Possible domain events:

```
UserRegistered

UserLoggedIn

ProfileCreated

ProfileUpdated

ConversationCreated

MessageAdded

DietPlanGenerated
```

Domain events represent important business facts.

---

# 10. Relationships

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

---

# 11. Persistence Mapping

## PostgreSQL

Identity context:

```
users

refresh_tokens
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
```

---

# 12. Domain Rules

The following rules must always be respected:

1. Business rules belong to the domain layer.

2. Database models are not domain models.

3. External services are accessed through abstractions.

4. Modules do not directly access each other's persistence.

5. New business capabilities should be added inside the correct bounded context.

6. Domain objects should not depend on frameworks.

---

# 13. Future Extensions

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

These should be introduced only when supported by real business requirements.