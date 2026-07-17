from backend.modules.ai.domain import AIResponse, Prompt


def test_prompt_defaults() -> None:
    prompt = Prompt(question="What should I eat?", category="BREAKFAST")

    assert prompt.conversation_history == ()
    assert prompt.system_context is None
    assert prompt.user_profile is None


def test_prompt_carries_conversation_history() -> None:
    prompt = Prompt(
        question="And tomorrow?",
        category="BREAKFAST",
        conversation_history=("USER: What should I eat?", "ASSISTANT: Try oatmeal."),
    )

    assert prompt.conversation_history == ("USER: What should I eat?", "ASSISTANT: Try oatmeal.")


def test_ai_response_fields() -> None:
    response = AIResponse(content="Try oatmeal.", model="mock", tokens=12, execution_time=0.01)

    assert response.content == "Try oatmeal."
    assert response.tokens == 12
