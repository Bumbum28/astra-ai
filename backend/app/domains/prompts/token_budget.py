from dataclasses import dataclass

from app.llm.contracts import LLMMessage, LLMMessageRole


@dataclass(frozen=True, slots=True)
class PromptBudgetResult:
    messages: list[LLMMessage]
    estimated_tokens: int
    dropped_messages: int
    truncated_system_messages: int


class PromptTokenBudgeter:
    """Apply a conservative local token budget without provider SDK coupling."""

    _CHARS_PER_TOKEN = 3
    _MESSAGE_OVERHEAD = 8
    _TRUNCATION_MARKER = "\n\n[Earlier prompt content truncated to fit context budget.]"

    def trim(
        self,
        messages: list[LLMMessage],
        *,
        token_budget: int,
    ) -> PromptBudgetResult:
        if not messages:
            return PromptBudgetResult([], 0, 0, 0)

        system_messages = [
            message for message in messages if message.role == LLMMessageRole.SYSTEM
        ]
        dialogue_messages = [
            message for message in messages if message.role != LLMMessageRole.SYSTEM
        ]
        selected_system, truncated = self._fit_system_messages(
            system_messages,
            max(512, int(token_budget * 0.55)),
        )
        used = sum(self.estimate_message(item) for item in selected_system)

        selected_dialogue: list[LLMMessage] = []
        remaining = max(0, token_budget - used)
        for message in reversed(dialogue_messages):
            cost = self.estimate_message(message)
            if cost <= remaining or not selected_dialogue:
                selected_dialogue.append(
                    message
                    if cost <= remaining
                    else self._truncate_message(message, remaining)
                )
                remaining = max(0, remaining - min(cost, remaining))
                continue
            break
        selected_dialogue.reverse()

        result = [*selected_system, *selected_dialogue]
        return PromptBudgetResult(
            messages=result,
            estimated_tokens=sum(self.estimate_message(item) for item in result),
            dropped_messages=max(0, len(messages) - len(result)),
            truncated_system_messages=truncated,
        )

    def estimate_message(self, message: LLMMessage) -> int:
        return self._MESSAGE_OVERHEAD + self.estimate_text(message.content)

    def estimate_text(self, text: str) -> int:
        return max(1, (len(text) + self._CHARS_PER_TOKEN - 1) // self._CHARS_PER_TOKEN)

    def _fit_system_messages(
        self,
        messages: list[LLMMessage],
        token_budget: int,
    ) -> tuple[list[LLMMessage], int]:
        if not messages:
            return [], 0
        per_message = max(128, token_budget // len(messages))
        selected: list[LLMMessage] = []
        truncated = 0
        for message in messages:
            if self.estimate_message(message) <= per_message:
                selected.append(message)
                continue
            selected.append(self._truncate_message(message, per_message))
            truncated += 1
        return selected, truncated

    def _truncate_message(self, message: LLMMessage, token_budget: int) -> LLMMessage:
        available_chars = max(
            64,
            (token_budget - self._MESSAGE_OVERHEAD) * self._CHARS_PER_TOKEN,
        )
        marker = self._TRUNCATION_MARKER
        content = message.content
        if len(content) > available_chars:
            content = content[: max(1, available_chars - len(marker))].rstrip() + marker
        return message.model_copy(update={"content": content})
