from app.domains.prompts.composer import StructuredPromptComposer
from app.domains.prompts.contracts import (
    CharacterPromptProfile,
    PersonaPromptProfile,
    RelationshipPromptState,
    RoleplayPromptContext,
)
from app.llm.contracts import LLMMessageRole


def test_structured_prompt_composer_orders_typed_sections() -> None:
    composer = StructuredPromptComposer()
    messages = composer.compose(
        RoleplayPromptContext(
            character=CharacterPromptProfile(
                name="Kael",
                summary="Một người bảo vệ.",
                personality="Kiềm chế.",
                speaking_style="Chậm rãi.",
                scenario="Thế giới băng giá.",
                greeting=None,
                system_instructions="Không tự mô tả hành động của user.",
            ),
            persona=PersonaPromptProfile(
                name="Ari",
                description="Người sống sót.",
                pronouns="hắn",
                background=None,
                traits=None,
                writing_style="Đoạn văn liền mạch.",
            ),
            relationship=RelationshipPromptState(
                level="l3",
                affection_score=42,
                status="Mập mờ",
                turn_count=8,
                context="Đã cùng thoát khỏi một cuộc truy đuổi.",
            ),
        ),
        "Giữ nhịp kể chậm.",
        "Anh là ai?",
    )

    assert len(messages) == 1
    assert messages[0].role == LLMMessageRole.SYSTEM
    content = messages[0].content
    assert content.index("# Character profile") < content.index("# User persona")
    assert content.index("# User persona") < content.index("# Relationship state")
    assert "Never decide, narrate, or invent the user's actions" in content
    assert "Kael" in content
    assert "Ari" in content
    assert "Relationship level: l3" in content
    assert content.endswith("Giữ nhịp kể chậm.")


def test_prompt_composer_uses_standard_mode_for_normal_vietnamese() -> None:
    messages = StructuredPromptComposer().compose(
        RoleplayPromptContext(),
        None,
        "Không phải như vậy, em vẫn nhớ anh mà.",
    )

    content = messages[0].content
    assert "Reply exclusively in Vietnamese" in content
    assert "Mode: standard Vietnamese" in content
    assert "Reply using complete words" in content
    assert "do not force teencode" in content
    assert "Never output Chinese characters" in content


def test_prompt_composer_mirrors_teencode_only_when_user_uses_it() -> None:
    messages = StructuredPromptComposer().compose(
        RoleplayPromptContext(),
        None,
        "ko phải đâu, em cx nhớ anh mà",
    )

    content = messages[0].content
    assert "Mode: Vietnamese teencode/shorthand" in content
    assert "may mirror a similar, moderate level" in content
    assert "Do not exaggerate" in content
