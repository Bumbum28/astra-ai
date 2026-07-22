#!/usr/bin/env python3
"""Run Astra's 30-case Vietnamese roleplay benchmark against the GPT pipeline."""

import argparse
import asyncio
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import AppConfig
from app.domains.chat.language_guard import VietnameseOutputGuard
from app.domains.intelligence.service import IntelligencePipeline
from app.llm.contracts import LLMMessage, LLMMessageRole, LLMRequest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "benchmarks" / "vietnamese_roleplay_cases.json"
TEENCODE_PATTERN = re.compile(
    r"(?i)(?<!\w)(ko|k|khum|cx|đc|dc|r|vs|bh|bt|lm|j|nx|s)(?!\w)"
)


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    title: str
    category: str
    passed: bool
    deterministic_score: float
    critic_score: float | None
    rewritten: bool
    checks: dict[str, bool]
    response: str
    latency_seconds: float
    error: str | None = None


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Benchmark file must contain a 'cases' list.")
    if len(cases) != 30:
        raise ValueError(f"Expected exactly 30 benchmark cases, found {len(cases)}.")

    identifiers: set[str] = set()
    required = {
        "id",
        "category",
        "title",
        "style_mode",
        "system_prompt",
        "history",
        "user_message",
        "expected_behaviors",
        "forbidden_phrases",
    }
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Case {index} must be an object.")
        missing = required.difference(case)
        if missing:
            raise ValueError(f"Case {index} is missing: {sorted(missing)}")
        identifier = str(case["id"])
        if identifier in identifiers:
            raise ValueError(f"Duplicate benchmark case id: {identifier}")
        identifiers.add(identifier)
        if case["style_mode"] not in {"standard", "teencode"}:
            raise ValueError(f"Case {identifier} has invalid style_mode.")
    return cases


def build_messages(case: dict[str, Any]) -> list[LLMMessage]:
    messages = [
        LLMMessage(
            role=LLMMessageRole.SYSTEM,
            content=(
                "Chỉ trả lời bằng tiếng Việt. Không dùng chữ Trung Quốc hoặc pinyin. "
                "Không tự quyết định hành động, suy nghĩ, cảm xúc hay lời thoại của "
                "người dùng. Hãy trả lời như một cuộc trò chuyện tự nhiên, không như "
                "một báo cáo API.\n\n" + str(case["system_prompt"])
            ),
        )
    ]
    for item in case["history"]:
        messages.append(
            LLMMessage(
                role=LLMMessageRole(str(item["role"])),
                content=str(item["content"]),
            )
        )
    messages.append(
        LLMMessage(role=LLMMessageRole.USER, content=str(case["user_message"]))
    )
    return messages


def deterministic_checks(
    case: dict[str, Any],
    response: str,
    guard: VietnameseOutputGuard,
) -> dict[str, bool]:
    normalized = response.casefold()
    forbidden = [str(item).casefold() for item in case["forbidden_phrases"]]
    checks = {
        "non_empty": bool(response.strip()),
        "no_forbidden_script": not guard.contains_forbidden_script(response),
        "no_forbidden_phrase": not any(item in normalized for item in forbidden),
        "not_meta_assistant": not any(
            phrase in normalized
            for phrase in ("tôi là ai", "tôi là một mô hình", "tôi có thể hỗ trợ")
        ),
    }
    if case["style_mode"] == "standard":
        checks["standard_style_preserved"] = TEENCODE_PATTERN.search(response) is None
    else:
        checks["teencode_understood"] = "không hiểu" not in normalized
    return checks


async def run_case(
    pipeline: IntelligencePipeline,
    config: AppConfig,
    case: dict[str, Any],
    guard: VietnameseOutputGuard,
) -> CaseResult:
    loop = asyncio.get_running_loop()
    started = loop.time()
    try:
        result = await pipeline.generate(
            "openai",
            LLMRequest(
                messages=build_messages(case),
                model=config.default_llm_model,
                max_tokens=min(config.chat_default_max_tokens, 2048),
                reasoning_effort=config.openai_reasoning_effort,
                store=False,
                metadata={
                    "benchmark_case_id": case["id"],
                    "benchmark_category": case["category"],
                },
            ),
        )
        checks = deterministic_checks(case, result.response.content, guard)
        score = sum(checks.values()) / len(checks)
        critic_score = result.critic_score
        passed = all(checks.values()) and (
            critic_score is None
            or critic_score >= config.intelligence_critic_score_threshold
            or result.rewritten
        )
        return CaseResult(
            case_id=str(case["id"]),
            title=str(case["title"]),
            category=str(case["category"]),
            passed=passed,
            deterministic_score=round(score, 4),
            critic_score=critic_score,
            rewritten=result.rewritten,
            checks=checks,
            response=result.response.content,
            latency_seconds=round(loop.time() - started, 3),
        )
    except Exception as exc:  # benchmark must continue after one failed API call
        return CaseResult(
            case_id=str(case["id"]),
            title=str(case["title"]),
            category=str(case["category"]),
            passed=False,
            deterministic_score=0.0,
            critic_score=None,
            rewritten=False,
            checks={},
            response="",
            latency_seconds=round(loop.time() - started, 3),
            error=f"{type(exc).__name__}: {exc}",
        )


async def run(args: argparse.Namespace) -> int:
    cases = load_cases(args.cases)
    print(f"Validated {len(cases)} Vietnamese benchmark cases.")
    if args.validate_only:
        return 0

    from app.llm.chat.service import ChatService
    from app.llm.factory import LLMFactory, build_default_registry
    from app.llm.resolver import LLMProviderResolver

    config = AppConfig()
    if config.openai_api_key is None or not config.openai_api_key.get_secret_value():
        print("OPENAI_API_KEY is required to run the live benchmark.", file=sys.stderr)
        return 2
    if config.default_llm_provider != "openai":
        print(
            "Warning: DEFAULT_LLM_PROVIDER is not 'openai'; "
            "benchmark still uses OpenAI."
        )

    registry = build_default_registry()
    resolver = LLMProviderResolver(LLMFactory(config, registry))
    pipeline = IntelligencePipeline(ChatService(resolver), config)
    guard = VietnameseOutputGuard()
    selected = cases[: args.limit]
    results: list[CaseResult] = []
    print(
        "Live benchmark may use 3-4 API calls per case "
        "(planner, draft, critic, optional rewrite)."
    )
    for index, case in enumerate(selected, start=1):
        print(f"[{index:02d}/{len(selected):02d}] {case['id']} - {case['title']}")
        result = await run_case(pipeline, config, case, guard)
        results.append(result)
        print(
            f"  {'PASS' if result.passed else 'FAIL'} | "
            f"critic={result.critic_score} | {result.latency_seconds}s"
        )

    passed = sum(item.passed for item in results)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": config.default_llm_model,
        "planner_model": config.intelligence_planner_model,
        "critic_model": config.intelligence_critic_model,
        "case_count": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4) if results else 0,
        "results": [asdict(item) for item in results],
    }
    output = args.output or (
        ROOT
        / "benchmarks"
        / "reports"
        / f"vietnamese-roleplay-{datetime.now(UTC):%Y%m%d-%H%M%S}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Result: {passed}/{len(results)} passed ({report['pass_rate']:.1%}).")
    print(f"Report: {output}")
    return 0 if passed == len(results) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--limit", type=int, default=30, choices=range(1, 31))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
