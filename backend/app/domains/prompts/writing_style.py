import re
from enum import StrEnum


class UserWritingStyle(StrEnum):
    STANDARD = "standard"
    TEENCODE = "teencode"


class VietnameseWritingStyleDetector:
    """Classify only explicit Vietnamese shorthand, not casual tone in general."""

    _token_pattern = re.compile(r"\w+", re.UNICODE)
    _strong_markers = frozenset(
        {
            "k",
            "ko",
            "khum",
            "hong",
            "hok",
            "hem",
            "dc",
            "đc",
            "cx",
            "mik",
            "mk",
            "j",
            "z",
            "zay",
            "zậy",
            "thui",
            "thoy",
            "rui",
            "rùi",
            "ntn",
        }
    )
    _weak_markers = frozenset(
        {
            "r",
            "vs",
            "th",
            "bh",
            "bt",
            "mn",
            "ms",
            "nch",
            "ns",
            "ib",
            "rep",
            "ny",
            "nyc",
            "ck",
            "vk",
        }
    )

    def detect(self, content: str | None) -> UserWritingStyle:
        if not content:
            return UserWritingStyle.STANDARD

        tokens = {
            token.casefold()
            for token in self._token_pattern.findall(content)
            if token
        }
        if tokens & self._strong_markers:
            return UserWritingStyle.TEENCODE
        if len(tokens & self._weak_markers) >= 2:
            return UserWritingStyle.TEENCODE
        return UserWritingStyle.STANDARD
