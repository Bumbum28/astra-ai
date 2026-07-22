from app.domains.chat.language_guard import VietnameseOutputGuard


def test_language_guard_keeps_vietnamese_text() -> None:
    guard = VietnameseOutputGuard()
    result = guard.sanitize("Ừ, mình cx nhớ cậu mà, đừng lo nha.")

    assert result.changed is False
    assert result.content == "Ừ, mình cx nhớ cậu mà, đừng lo nha."


def test_language_guard_removes_cjk_from_mixed_text() -> None:
    guard = VietnameseOutputGuard()
    result = guard.sanitize("Mình cx nhớ cậu. 我也想你。")

    assert result.changed is True
    assert "我" not in result.content
    assert "想" not in result.content
    assert "Mình cx nhớ cậu" in result.content


def test_language_guard_uses_vietnamese_fallback_for_all_cjk_text() -> None:
    guard = VietnameseOutputGuard()
    result = guard.sanitize("我也很想你。")

    assert result.changed is True
    assert result.content == guard.fallback_message
