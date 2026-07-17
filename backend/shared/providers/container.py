from typing import Any

from backend.shared.providers.ai import LLMProvider, MockLLMProvider


class DIContainer:
    """Prosty DI container."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Zarejestruj usługę."""
        self._services[name] = service

    def get(self, name: str) -> Any:
        """Pobierz zarejestrowaną usługę."""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered in DI container")
        return self._services[name]


def create_di_container(use_mock_ai: bool = True) -> DIContainer:
    """Utwórz i zaregistruj wszystkie providery."""
    container = DIContainer()

    # AI Provider
    ai_provider: LLMProvider = MockLLMProvider() if use_mock_ai else MockLLMProvider()
    container.register("ai_provider", ai_provider)

    return container