from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Prompt:
    question: str
    category: str
    conversation_history: tuple[str, ...] = field(default_factory=tuple)
    system_context: str | None = None
    user_profile: str | None = None
