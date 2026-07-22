import json
from dataclasses import dataclass
from typing import cast

from app.core.config import AppConfig
from app.domains.intelligence.models import CriticVerdict, ResponsePlan
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.contracts import (
    LLMMessage,
    LLMMessageRole,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from app.llm.contracts.request import ReasoningEffort


@dataclass(frozen=True, slots=True)
class IntelligenceResult:
    response: LLMResponse
    planner_used: bool
    critic_used: bool
    rewritten: bool
    critic_score: float | None


class IntelligencePipeline:
    """Plan, draft, critique, and optionally rewrite hidden analysis."""

    _PLANNER_INSTRUCTION = (
        "You are Astra's response director. Produce only the requested structured "
        "response plan. Do not write the final answer and do not provide chain-of-"
        "thought. Infer the user's intent, emotional subtext, continuity facts, "
        "what must be addressed, a concise response strategy, forbidden moves, and "
        "style guidance. Preserve user autonomy: never plan actions, thoughts, "
        "feelings, or dialogue for the user. The final answer must be Vietnamese and "
        "must mirror teencode only when the latest user message uses it."
    )

    _CRITIC_INSTRUCTION = (
        "You are Astra's strict response critic. Evaluate the candidate against the "
        "conversation, system rules, character, persona, relationship state, and "
        "response plan. Check relevance, intelligence, emotional understanding, "
        "continuity, non-repetition, natural Vietnamese, adaptive writing style, "
        "absence of Chinese text or pinyin, and preservation of user autonomy. "
        "Approve only when the answer is ready to show. Return only the requested "
        "structured verdict; do not reveal chain-of-thought."
    )

    def __init__(self, llm_service: LLMChatService, config: AppConfig) -> None:
        self._llm_service = llm_service
        self._config = config

    async def generate(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> IntelligenceResult:
        if not self._config.intelligence_enabled:
            response = await self._llm_service.generate(provider_name, request)
            return IntelligenceResult(response, False, False, False, None)

        plan, planner_usage = await self._create_plan(request)
        draft_request = self._build_draft_request(request, plan)
        draft = await self._llm_service.generate(provider_name, draft_request)

        verdict, critic_usage = await self._critique(request, plan, draft)
        accumulated_usage = self._merge_many_usage(
            planner_usage, draft.usage, critic_usage
        )
        draft = draft.model_copy(update={"usage": accumulated_usage})
        if verdict is None:
            return IntelligenceResult(
                self._annotate(
                    draft,
                    planner_used=plan is not None,
                    critic_used=False,
                    rewritten=False,
                    critic_score=None,
                ),
                plan is not None,
                False,
                False,
                None,
            )

        threshold = self._config.intelligence_critic_score_threshold
        if verdict.approved and verdict.score >= threshold:
            response = self._annotate(
                draft,
                planner_used=plan is not None,
                critic_used=True,
                rewritten=False,
                critic_score=verdict.score,
                critic_issues=verdict.issues,
            )
            return IntelligenceResult(
                response, plan is not None, True, False, verdict.score
            )

        if self._config.intelligence_max_rewrite_attempts < 1:
            response = self._annotate(
                draft,
                planner_used=plan is not None,
                critic_used=True,
                rewritten=False,
                critic_score=verdict.score,
                critic_issues=verdict.issues,
            )
            return IntelligenceResult(
                response, plan is not None, True, False, verdict.score
            )

        rewritten_request = self._build_rewrite_request(
            request,
            plan,
            draft.content,
            verdict,
        )
        try:
            rewritten = await self._llm_service.generate(
                provider_name, rewritten_request
            )
        except Exception:
            response = self._annotate(
                draft,
                planner_used=plan is not None,
                critic_used=True,
                rewritten=False,
                critic_score=verdict.score,
                critic_issues=verdict.issues,
                extra_metadata={"rewrite_failed": True},
            )
            return IntelligenceResult(
                response, plan is not None, True, False, verdict.score
            )

        rewritten = rewritten.model_copy(
            update={
                "usage": self._merge_usage(draft.usage, rewritten.usage),
            }
        )
        response = self._annotate(
            rewritten,
            planner_used=plan is not None,
            critic_used=True,
            rewritten=True,
            critic_score=verdict.score,
            critic_issues=verdict.issues,
        )
        return IntelligenceResult(response, plan is not None, True, True, verdict.score)

    async def _create_plan(
        self, request: LLMRequest
    ) -> tuple[ResponsePlan | None, LLMUsage | None]:
        planner_request = LLMRequest(
            messages=[
                LLMMessage(
                    role=LLMMessageRole.SYSTEM,
                    content=self._PLANNER_INSTRUCTION,
                ),
                *request.messages,
            ],
            model=self._config.intelligence_planner_model,
            max_tokens=self._config.intelligence_planner_max_tokens,
            reasoning_effort=self._reasoning_effort(
                self._config.intelligence_planner_reasoning_effort
            ),
            response_schema_name="astra_response_plan",
            response_schema=ResponsePlan.model_json_schema(),
            store=False,
            metadata={"intelligence_stage": "planner"},
        )
        try:
            response = await self._llm_service.generate(
                self._config.intelligence_provider,
                planner_request,
            )
            return ResponsePlan.model_validate_json(response.content), response.usage
        except Exception:
            return None, None

    async def _critique(
        self,
        request: LLMRequest,
        plan: ResponsePlan | None,
        draft: LLMResponse,
    ) -> tuple[CriticVerdict | None, LLMUsage | None]:
        plan_text = self._plan_text(plan) if plan is not None else "No plan available."
        candidate = draft.content[-12000:]
        critic_request = LLMRequest(
            messages=[
                LLMMessage(
                    role=LLMMessageRole.SYSTEM,
                    content=self._CRITIC_INSTRUCTION,
                ),
                *request.messages,
                LLMMessage(
                    role=LLMMessageRole.USER,
                    content=(
                        "Evaluate this hidden response plan and candidate answer.\n\n"
                        f"PLAN:\n{plan_text}\n\nCANDIDATE:\n{candidate}"
                    ),
                ),
            ],
            model=self._config.intelligence_critic_model,
            max_tokens=self._config.intelligence_critic_max_tokens,
            reasoning_effort=self._reasoning_effort(
                self._config.intelligence_critic_reasoning_effort
            ),
            response_schema_name="astra_critic_verdict",
            response_schema=CriticVerdict.model_json_schema(),
            store=False,
            metadata={"intelligence_stage": "critic"},
        )
        try:
            response = await self._llm_service.generate(
                self._config.intelligence_provider,
                critic_request,
            )
            return CriticVerdict.model_validate_json(response.content), response.usage
        except Exception:
            return None, None

    def _build_draft_request(
        self,
        request: LLMRequest,
        plan: ResponsePlan | None,
    ) -> LLMRequest:
        messages = request.messages
        if plan is not None:
            messages = [
                LLMMessage(
                    role=LLMMessageRole.SYSTEM,
                    content=(
                        "# Hidden response plan\n"
                        "Use this concise plan internally. Do not mention the plan or "
                        "analysis in the final answer.\n"
                        + self._plan_text(plan)
                    ),
                ),
                *messages,
            ]
        return request.model_copy(
            update={
                "messages": messages,
                "reasoning_effort": self._reasoning_effort(
                    self._config.intelligence_generation_reasoning_effort
                ),
                "store": False,
                "metadata": {
                    **request.metadata,
                    "intelligence_stage": "draft",
                },
            }
        )

    def _build_rewrite_request(
        self,
        request: LLMRequest,
        plan: ResponsePlan | None,
        draft: str,
        verdict: CriticVerdict,
    ) -> LLMRequest:
        issues = (
            "\n".join(f"- {item}" for item in verdict.issues)
            or "- Improve quality."
        )
        instruction = verdict.rewrite_instruction or "Rewrite to resolve every issue."
        rewrite_system = LLMMessage(
            role=LLMMessageRole.SYSTEM,
            content=(
                "# Mandatory final rewrite\n"
                "Rewrite the candidate from scratch. Do not mention the critic, score, "
                "plan, or rewrite process. Preserve all roleplay and language rules.\n"
                f"Critic issues:\n{issues}\n"
                f"Rewrite instruction: {instruction}\n"
                f"Hidden plan: {self._plan_text(plan) if plan else 'Unavailable'}\n"
                f"Rejected candidate:\n{draft[-12000:]}"
            ),
        )
        return request.model_copy(
            update={
                "messages": [rewrite_system, *request.messages],
                "temperature": min(request.temperature or 0.7, 0.7),
                "reasoning_effort": self._reasoning_effort(
                    self._config.intelligence_generation_reasoning_effort
                ),
                "store": False,
                "metadata": {
                    **request.metadata,
                    "intelligence_stage": "rewrite",
                },
            }
        )

    @staticmethod
    def _plan_text(plan: ResponsePlan) -> str:
        payload = plan.model_dump(mode="json")
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _reasoning_effort(value: str) -> ReasoningEffort:
        allowed = {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
        normalized = value if value in allowed else "medium"
        return cast(ReasoningEffort, normalized)

    @staticmethod
    def _merge_usage(left: LLMUsage | None, right: LLMUsage | None) -> LLMUsage | None:
        if left is None:
            return right
        if right is None:
            return left

        def total(first: int | None, second: int | None) -> int | None:
            if first is None and second is None:
                return None
            return (first or 0) + (second or 0)

        return LLMUsage(
            input_tokens=total(left.input_tokens, right.input_tokens),
            output_tokens=total(left.output_tokens, right.output_tokens),
            total_tokens=total(left.total_tokens, right.total_tokens),
        )

    @classmethod
    def _merge_many_usage(cls, *items: LLMUsage | None) -> LLMUsage | None:
        merged: LLMUsage | None = None
        for item in items:
            merged = cls._merge_usage(merged, item)
        return merged

    def _annotate(
        self,
        response: LLMResponse,
        *,
        planner_used: bool,
        critic_used: bool,
        rewritten: bool,
        critic_score: float | None,
        critic_issues: list[str] | None = None,
        extra_metadata: dict[str, object] | None = None,
    ) -> LLMResponse:
        return response.model_copy(
            update={
                "metadata": {
                    **response.metadata,
                    "intelligence_enabled": True,
                    "intelligence_pipeline_version": "1",
                    "intelligence_planner_model": (
                        self._config.intelligence_planner_model
                    ),
                    "intelligence_critic_model": (
                        self._config.intelligence_critic_model
                    ),
                    "planner_used": planner_used,
                    "critic_used": critic_used,
                    "rewritten": rewritten,
                    "critic_score": critic_score,
                    "critic_issue_count": len(critic_issues or []),
                    **(extra_metadata or {}),
                }
            }
        )
