from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException, ValidationException
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.relationships.model import RelationshipEvent, RelationshipLevel
from app.domains.relationships.schemas import (
    RelationshipEventResponse,
    RelationshipHistoryResponse,
    RelationshipResponse,
    RelationshipUpdateRequest,
)


class RelationshipService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(
        self,
        user_id: UUID,
        conversation_id: UUID,
    ) -> RelationshipResponse:
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(conversation_id, user_id)
            if conversation is None:
                raise NotFoundException(
                    "Conversation was not found.",
                    code=ErrorCode.CONVERSATION_NOT_FOUND,
                )
            relationship = await uow.relationships.get_by_conversation(conversation_id)
            if relationship is None:
                raise self._not_found()
            return RelationshipResponse.model_validate(relationship)

    async def update(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request: RelationshipUpdateRequest,
    ) -> RelationshipResponse:
        fields = request.model_fields_set
        mutable_fields = fields & {"level", "affection_score", "status", "context"}
        if not mutable_fields:
            raise ValidationException("At least one relationship field must change.")

        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(
                conversation_id,
                user_id,
                for_update=True,
            )
            if conversation is None:
                raise NotFoundException(
                    "Conversation was not found.",
                    code=ErrorCode.CONVERSATION_NOT_FOUND,
                )
            relationship = await uow.relationships.get_by_conversation(
                conversation_id,
                for_update=True,
            )
            if relationship is None:
                raise self._not_found()

            previous_level = relationship.level
            previous_score = relationship.affection_score
            if "level" in fields and request.level is not None:
                relationship.level = request.level.value
            if "affection_score" in fields and request.affection_score is not None:
                relationship.affection_score = request.affection_score
            if "status" in fields:
                relationship.status = request.status
            if "context" in fields:
                relationship.context = request.context
            relationship.last_change_reason = request.reason

            event = RelationshipEvent(
                id=uuid4(),
                relationship_id=relationship.id,
                source_message_id=None,
                previous_level=previous_level,
                new_level=relationship.level,
                previous_score=previous_score,
                new_score=relationship.affection_score,
                score_delta=relationship.affection_score - previous_score,
                reason=request.reason,
                event_metadata=request.metadata,
            )
            await uow.relationship_events.add(event)
            await uow.flush()
            response = RelationshipResponse.model_validate(relationship)
            await uow.commit()
            return response

    async def history(
        self,
        user_id: UUID,
        conversation_id: UUID,
        *,
        limit: int,
    ) -> RelationshipHistoryResponse:
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(conversation_id, user_id)
            if conversation is None:
                raise NotFoundException(
                    "Conversation was not found.",
                    code=ErrorCode.CONVERSATION_NOT_FOUND,
                )
            relationship = await uow.relationships.get_by_conversation(conversation_id)
            if relationship is None:
                raise self._not_found()
            events = await uow.relationship_events.list_for_relationship(
                relationship.id,
                limit=min(limit, 100),
            )
            return RelationshipHistoryResponse(
                items=[
                    RelationshipEventResponse.model_validate(item) for item in events
                ]
            )

    def _not_found(self) -> NotFoundException:
        return NotFoundException(
            "Relationship was not found for this conversation.",
            code=ErrorCode.RELATIONSHIP_NOT_FOUND,
        )
