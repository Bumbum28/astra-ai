from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.characters.model import Character
from app.domains.characters.schemas import (
    CharacterCreateRequest,
    CharacterListResponse,
    CharacterResponse,
    CharacterUpdateRequest,
)


class CharacterService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self, user_id: UUID, request: CharacterCreateRequest
    ) -> CharacterResponse:
        """Create a user-owned roleplay character."""
        character = Character(
            id=uuid4(),
            user_id=user_id,
            name=request.name,
            tagline=request.tagline,
            description=request.description,
            personality=request.personality,
            scenario=request.scenario,
            system_prompt=request.system_prompt,
            greeting=request.greeting,
            avatar_url=request.avatar_url,
            is_active=True,
            character_metadata=request.metadata,
        )
        async with self._uow_factory() as uow:
            await uow.characters.add(character)
            await uow.flush()
            response = CharacterResponse.model_validate(character)
            await uow.commit()
            return response

    async def list_for_user(self, user_id: UUID) -> CharacterListResponse:
        """List active characters owned by the current user."""
        async with self._uow_factory() as uow:
            items = await uow.characters.list_for_user(user_id)
        return CharacterListResponse(
            items=[CharacterResponse.model_validate(item) for item in items]
        )

    async def get(self, user_id: UUID, character_id: UUID) -> CharacterResponse:
        """Return a character only when it belongs to the current user."""
        async with self._uow_factory() as uow:
            character = await uow.characters.get_owned(character_id, user_id)
            if character is None:
                raise self._not_found()
            return CharacterResponse.model_validate(character)

    async def update(
        self,
        user_id: UUID,
        character_id: UUID,
        request: CharacterUpdateRequest,
    ) -> CharacterResponse:
        """Update a character while preserving ownership boundaries."""
        async with self._uow_factory() as uow:
            character = await uow.characters.get_owned(
                character_id, user_id, include_inactive=True, for_update=True
            )
            if character is None:
                raise self._not_found()
            for field in request.model_fields_set:
                if field == "metadata":
                    character.character_metadata = request.metadata or {}
                else:
                    setattr(character, field, getattr(request, field))
            await uow.flush()
            response = CharacterResponse.model_validate(character)
            await uow.commit()
            return response

    async def archive(self, user_id: UUID, character_id: UUID) -> None:
        """Soft-disable a character without deleting historical conversations."""
        async with self._uow_factory() as uow:
            character = await uow.characters.get_owned(
                character_id, user_id, include_inactive=True, for_update=True
            )
            if character is None:
                raise self._not_found()
            character.is_active = False
            await uow.commit()

    @staticmethod
    def _not_found() -> NotFoundException:
        return NotFoundException(
            "Character was not found.", code=ErrorCode.CHARACTER_NOT_FOUND
        )
