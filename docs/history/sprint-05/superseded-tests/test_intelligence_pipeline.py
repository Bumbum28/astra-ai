import json

import pytest

from app.core.config import AppConfig
from app.domains.intelligence.models import CriticVerdict, ResponsePlan
from app.domains.intelligence.service import IntelligencePipeline
from app.llm.contracts import (
    LLMMessage,
    LLMMessageRole,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)


class StageAwareLLMService:
    def __init__(self, *, approved: bool, fail_rewrite: bool = False) -> None:
        self.approved = approved
        self.fail_rewrite = fail_rewrite
        self.calls: list[tuple[str, LLMRequest]] = []

    async def generate(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> LLMResponse:
        self.calls.append((provider_name, request))
        stage = request.metadata.get("intelligence_stage")
        if stage == "planner":
            content = json.dumps(
                {
                    "user_intent": "Muốn được trấn an",
                    "emotional_subtext": "Hơi bất an",
                    "continuity_facts": ["Hai người đang thân thiết"],
                    "must_address": ["Xác nhận cảm xúc"],
                    "response_strategy": ["Trả lời trực tiếp và ấm áp"],
                    "forbidden_moves": ["Không điều khiển user"],
                    "style_guidance": "Tiếng Việt đầy đủ",
                },
                ensure_ascii=False,
            )
            return LLMResponse(
                content=content,
                model="gpt-5.6-luna",
                provider="openai",
                usage=LLMUsage(input_tokens=10, output_tokens=2, total_tokens=12),
            )
        if stage == "critic":
            content = json.dumps(
                {
                    "approved": self.approved,
                    "score": 0.95 if self.approved else 0.4,
                    "issues": [] if self.approved else ["Câu trả lời quá chung chung"],
                    "rewrite_instruction": "Trả lời cụ thể và tự nhiên hơn",
                },
                ensure_ascii=False,
            )
            return LLMResponse(
                content=content,
                model="gpt-5.6-luna",
                provider="openai",
                usage=LLMUsage(input_tokens=10, output_tokens=2, total_tokens=12),
            )
        if stage == "rewrite":
            if self.fail_rewrite:
                raise RuntimeError("rewrite unavailable")
            return LLMResponse(
                content="Anh vẫn nhớ em, và anh muốn nghe em kể tiếp.",
                model="gpt-5.6-terra",
                provider=provider_name,
                usage=LLMUsage(input_tokens=20, output_tokens=4, total_tokens=24),
            )
        return LLMResponse(
            content="Anh nhớ em.",
            model="gpt-5.6-terra",
            provider=provider_name,
            usage=LLMUsage(input_tokens=20, output_tokens=3, total_tokens=23),
        )


@pytest.mark.asyncio
async def test_pipeline_uses_plan_and_accepts_good_draft() -> None:
    llm = StageAwareLLMService(approved=True)
    pipeline = IntelligencePipeline(
        llm, AppConfig(intelligence_enabled=True)
    )  # type: ignore[arg-type]
    result = await pipeline.generate(
        "openai",
        LLMRequest(
            messages=[
                LLMMessage(
                    role=LLMMessageRole.USER,
                    content="Anh còn nhớ em không?",
                )
            ],
            model="gpt-5.6-terra",
        ),
    )

    assert result.response.content == "Anh nhớ em."
    assert result.planner_used is True
    assert result.critic_used is True
    assert result.rewritten is False
    assert result.response.usage is not None
    assert result.response.usage.total_tokens == 47
    assert result.response.metadata["intelligence_pipeline_version"] == "1"
    assert result.response.metadata["intelligence_planner_model"] == "gpt-5.6-luna"
    assert len(llm.calls) == 3
    assert llm.calls[0][0] == "openai"
    assert llm.calls[0][1].response_schema_name == "astra_response_plan"


@pytest.mark.asyncio
async def test_pipeline_rewrites_failed_draft() -> None:
    llm = StageAwareLLMService(approved=False)
    pipeline = IntelligencePipeline(
        llm, AppConfig(intelligence_enabled=True)
    )  # type: ignore[arg-type]
    result = await pipeline.generate(
        "openai",
        LLMRequest(
            messages=[
                LLMMessage(
                    role=LLMMessageRole.USER,
                    content="Anh còn nhớ em không?",
                )
            ],
            model="gpt-5.6-terra",
        ),
    )

    assert result.response.content.startswith("Anh vẫn nhớ em")
    assert result.rewritten is True
    assert result.response.metadata["critic_score"] == 0.4
    assert result.response.usage is not None
    assert result.response.usage.total_tokens == 71
    assert len(llm.calls) == 4


@pytest.mark.asyncio
async def test_pipeline_returns_draft_when_rewrite_call_fails() -> None:
    llm = StageAwareLLMService(approved=False, fail_rewrite=True)
    pipeline = IntelligencePipeline(
        llm, AppConfig(intelligence_enabled=True)
    )  # type: ignore[arg-type]

    result = await pipeline.generate(
        "openai",
        LLMRequest(
            messages=[
                LLMMessage(
                    role=LLMMessageRole.USER,
                    content="Anh còn nhớ em không?",
                )
            ],
            model="gpt-5.6-terra",
        ),
    )

    assert result.response.content == "Anh nhớ em."
    assert result.rewritten is False
    assert result.response.metadata["rewrite_failed"] is True
    assert result.response.usage is not None
    assert result.response.usage.total_tokens == 47


def test_structured_contracts_require_every_property() -> None:
    for contract in (ResponsePlan, CriticVerdict):
        schema = contract.model_json_schema()
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
