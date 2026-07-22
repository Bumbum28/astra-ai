import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuardedText:
    content: str
    changed: bool


class VietnameseOutputGuard:
    """Prevent CJK-script output from reaching persistence or clients."""

    fallback_message = (
        "Mình vừa gặp lỗi ngôn ngữ nên chưa thể trả lời đúng. "
        "Bạn gửi lại tin nhắn giúp mình nhé."
    )

    _forbidden_scripts = re.compile(
        "["
        "\\u3040-\\u30ff"  # Hiragana and Katakana
        "\\u31f0-\\u31ff"  # Katakana extensions
        "\\u3400-\\u4dbf"  # CJK extension A
        "\\u4e00-\\u9fff"  # CJK unified ideographs
        "\\uf900-\\ufaff"  # CJK compatibility ideographs
        "]"
    )
    _cjk_punctuation = re.compile("[\\u3000-\\u303f\\uff01-\\uff65]")
    _horizontal_space = re.compile(r"[ \t]{2,}")
    _excess_blank_lines = re.compile(r"\n{3,}")

    def contains_forbidden_script(self, content: str) -> bool:
        return bool(
            self._forbidden_scripts.search(content)
            or self._cjk_punctuation.search(content)
        )

    def sanitize_fragment(self, content: str) -> GuardedText:
        """Remove forbidden scripts without injecting a fallback into a stream."""
        if not self.contains_forbidden_script(content):
            return GuardedText(content=content, changed=False)

        sanitized = self._forbidden_scripts.sub("", content)
        sanitized = self._cjk_punctuation.sub(" ", sanitized)
        sanitized = self._horizontal_space.sub(" ", sanitized)
        sanitized = self._excess_blank_lines.sub("\n\n", sanitized)
        return GuardedText(content=sanitized, changed=True)

    def sanitize(self, content: str) -> GuardedText:
        guarded = self.sanitize_fragment(content)
        sanitized = guarded.content.strip()
        if guarded.changed and not self._has_meaningful_text(sanitized):
            sanitized = self.fallback_message
        return GuardedText(content=sanitized, changed=guarded.changed)

    @staticmethod
    def _has_meaningful_text(content: str) -> bool:
        return sum(character.isalnum() for character in content) >= 8
