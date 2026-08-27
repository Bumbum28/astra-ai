from pathlib import Path

from scripts.run_vietnamese_benchmark import load_cases


def test_vietnamese_benchmark_has_exactly_30_valid_cases() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "benchmarks"
        / "vietnamese_roleplay_cases.json"
    )

    cases = load_cases(path)

    assert len(cases) == 30
    assert len({str(case["id"]) for case in cases}) == 30
    assert {str(case["style_mode"]) for case in cases} == {"standard", "teencode"}
