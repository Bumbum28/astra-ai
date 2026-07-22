from app.domains.prompts.token_budget import PromptTokenBudgeter
from app.llm.contracts import LLMMessage, LLMMessageRole


def test_budgeter_keeps_system_and_latest_dialogue() -> None:
    budgeter = PromptTokenBudgeter()
    messages = [
        LLMMessage(role=LLMMessageRole.SYSTEM, content="core rules" * 50),
        *[
            LLMMessage(
                role=(
                    LLMMessageRole.USER
                    if index % 2 == 0
                    else LLMMessageRole.ASSISTANT
                ),
                content=f"message-{index} " + ("x" * 400),
            )
            for index in range(20)
        ],
    ]

    result = budgeter.trim(messages, token_budget=1200)

    assert result.messages[0].role == LLMMessageRole.SYSTEM
    assert result.messages[-1].content.startswith("message-19")
    assert result.estimated_tokens <= 1300
    assert result.dropped_messages > 0


def test_budgeter_truncates_oversized_system_prompt() -> None:
    budgeter = PromptTokenBudgeter()
    result = budgeter.trim(
        [
            LLMMessage(role=LLMMessageRole.SYSTEM, content="A" * 30000),
            LLMMessage(role=LLMMessageRole.USER, content="hello"),
        ],
        token_budget=2048,
    )

    assert result.truncated_system_messages == 1
    assert "truncated" in result.messages[0].content
    assert result.messages[-1].content == "hello"
