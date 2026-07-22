from pydantic import BaseModel, ConfigDict, Field


class ResponsePlan(BaseModel):
    """A concise response strategy, not hidden chain-of-thought."""

    model_config = ConfigDict(extra="forbid")

    user_intent: str = Field(min_length=1, max_length=500)
    emotional_subtext: str = Field(max_length=500)
    continuity_facts: list[str] = Field(max_length=8)
    must_address: list[str] = Field(max_length=6)
    response_strategy: list[str] = Field(max_length=6)
    forbidden_moves: list[str] = Field(max_length=6)
    style_guidance: str = Field(max_length=500)


class CriticVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    score: float = Field(ge=0, le=1)
    issues: list[str] = Field(max_length=8)
    rewrite_instruction: str = Field(max_length=1000)
