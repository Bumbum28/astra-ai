from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextChunk:
    ordinal: int
    content: str


def chunk_text(text: str, *, size: int, overlap: int) -> list[TextChunk]:
    """Split text deterministically while preferring whitespace boundaries."""
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and smaller than size")
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[TextChunk] = []
    start = 0
    ordinal = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start + max(size // 2, 1), end)
            if boundary > start:
                end = boundary
        content = normalized[start:end].strip()
        if content:
            chunks.append(TextChunk(ordinal=ordinal, content=content))
            ordinal += 1
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks
