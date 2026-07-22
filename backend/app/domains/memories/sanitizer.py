import re
import unicodedata


class MemorySanitizer:
    """Reject credentials, redact summaries, and normalize stable memory keys."""

    _API_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
    _SECRET_LABEL = re.compile(
        r"\b(?:password|mật khẩu|api[_ -]?key|seed phrase|recovery phrase)\s*[:=]",
        re.I,
    )
    _SECRET_LINE = re.compile(
        r"(?im)^.*(?:password|mật khẩu|api[_ -]?key|seed phrase|recovery phrase)"
        r"\s*[:=].*$"
    )
    _KEY_PATTERN = re.compile(r"[^a-z0-9._:-]+")

    def is_safe(self, content: str) -> bool:
        normalized = content.strip()
        if not normalized:
            return False
        return not (
            self._API_KEY.search(normalized) or self._SECRET_LABEL.search(normalized)
        )

    def redact_secrets(self, content: str) -> str:
        redacted = self._API_KEY.sub("[REDACTED]", content)
        return self._SECRET_LINE.sub("[REDACTED]", redacted)

    def normalize_key(self, value: str) -> str:
        source = value.strip().lower().replace("đ", "d")
        key = unicodedata.normalize("NFKD", source).encode(
            "ascii", "ignore"
        ).decode("ascii")
        key = self._KEY_PATTERN.sub("-", key).strip("-")
        return key[:255] or "memory"
