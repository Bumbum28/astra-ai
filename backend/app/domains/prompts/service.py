from app.core.unit_of_work import UnitOfWork
from app.domains.conversations.model import Conversation
from app.domains.prompts.contracts import (
    CharacterPromptProfile,
    PersonaPromptProfile,
    RelationshipPromptState,
    RoleplayPromptContext,
)


class RoleplayPromptContextResolver:
    async def resolve(
        self,
        uow: UnitOfWork,
        conversation: Conversation,
    ) -> RoleplayPromptContext:
        character = None
        if conversation.character_version_id is not None:
            version = await uow.character_versions.get_by_id(
                conversation.character_version_id
            )
            if version is not None:
                character = CharacterPromptProfile(
                    name=version.name,
                    summary=version.summary,
                    personality=version.personality,
                    speaking_style=version.speaking_style,
                    scenario=version.scenario,
                    greeting=version.greeting,
                    system_instructions=version.system_instructions,
                )

        persona = None
        if conversation.persona_version_id is not None:
            version = await uow.persona_versions.get_by_id(
                conversation.persona_version_id
            )
            if version is not None:
                persona = PersonaPromptProfile(
                    name=version.name,
                    description=version.description,
                    pronouns=version.pronouns,
                    background=version.background,
                    traits=version.traits,
                    writing_style=version.writing_style,
                )

        relationship = None
        relationship_model = await uow.relationships.get_by_conversation(
            conversation.id
        )
        if relationship_model is not None:
            relationship = RelationshipPromptState(
                level=relationship_model.level,
                affection_score=relationship_model.affection_score,
                status=relationship_model.status,
                turn_count=relationship_model.turn_count,
                context=relationship_model.context,
            )

        return RoleplayPromptContext(
            character=character,
            persona=persona,
            relationship=relationship,
        )
