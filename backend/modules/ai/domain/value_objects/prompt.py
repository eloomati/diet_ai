from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PromptTurn:
    role: str  # "user" | "assistant"
    content: str


@dataclass(frozen=True, slots=True)
class Prompt:
    question: str
    category: str
    conversation_history: tuple[PromptTurn, ...] = field(default_factory=tuple)
    system_context: str | None = None
    user_profile: str | None = None
