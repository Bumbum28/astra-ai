from app.domains.prompts.writing_style import (
    UserWritingStyle,
    VietnameseWritingStyleDetector,
)


def test_detector_identifies_explicit_teencode() -> None:
    detector = VietnameseWritingStyleDetector()

    assert detector.detect("ko phải đâu, t cx nhớ mà") == UserWritingStyle.TEENCODE
    assert detector.detect("em nhắn vs anh r mà") == UserWritingStyle.TEENCODE


def test_detector_keeps_normal_vietnamese_in_standard_mode() -> None:
    detector = VietnameseWritingStyleDetector()

    assert (
        detector.detect("Không phải như vậy, em vẫn nhớ anh mà.")
        == UserWritingStyle.STANDARD
    )
