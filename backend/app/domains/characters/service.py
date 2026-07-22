from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException, ValidationException
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.characters.model import Character, CharacterVersion
from app.domains.characters.schemas import (
    CharacterCreateRequest,
    CharacterPageResponse,
    CharacterResponse,
    CharacterUpdateRequest,
)
from app.llm.registry import LLMProviderName
from app.utils.cursors import CursorPosition, decode_cursor, encode_cursor


class CharacterService:
    _version_fields = {
        "name",
        "summary",
        "personality",
        "speaking_style",
        "scenario",
        "greeting",
        "system_instructions",
    }
    _root_fields = {
        "avatar_url",
        "provider",
        "model",
        "temperature",
        "max_tokens",
    }

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        user_id: UUID,
        request: CharacterCreateRequest,
    ) -> CharacterResponse:
        self._validate_provider(request.provider)
        character = Character(
            id=uuid4(),
            user_id=user_id,
            current_version=1,
            avatar_url=request.avatar_url,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            character_metadata=request.metadata,
        )
        version = CharacterVersion(
            id=uuid4(),
            character_id=character.id,
            version=1,
            name=request.name,
            summary=request.summary,
            personality=request.personality,
            speaking_style=request.speaking_style,
            scenario=request.scenario,
            greeting=request.greeting,
            system_instructions=request.system_instructions,
            version_metadata={},
        )
        async with self._uow_factory() as uow:
            await uow.characters.add(character)
            await uow.character_versions.add(version)
            await uow.flush()
            response = self._response(character, version)
            await uow.commit()
            return response

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: str | None,
    ) -> CharacterPageResponse:
        page_size = min(limit, 100)
        decoded = decode_cursor(cursor) if cursor else None
        async with self._uow_factory() as uow:
            roots = list(
                await uow.characters.list_for_user(
                    user_id,
                    limit=page_size + 1,
                    cursor=decoded,
                )
            )
            has_more = len(roots) > page_size
            roots = roots[:page_size]
            versions = await uow.character_versions.list_current(roots)

        versions_by_character = {item.character_id: item for item in versions}
        responses = [
            self._response(root, self._require_version(versions_by_character, root.id))
            for root in roots
        ]
        next_cursor = None
        if has_more and roots:
            last = roots[-1]
            next_cursor = encode_cursor(
                CursorPosition(timestamp=last.updated_at, entity_id=last.id)
            )
        return CharacterPageResponse(items=responses, next_cursor=next_cursor)

    async def get(self, user_id: UUID, character_id: UUID) -> CharacterResponse:
        async with self._uow_factory() as uow:
            character = await uow.characters.get_owned(character_id, user_id)
            if character is None:
                raise self._not_found()
            version = await uow.character_versions.get_version(
                character.id,
                character.current_version,
            )
            if version is None:
                raise RuntimeError("Character current version is missing.")
            return self._response(character, version)

    async def update(
        self,
        user_id: UUID,
        character_id: UUID,
        request: CharacterUpdateRequest,
    ) -> CharacterResponse:
        fields = request.model_fields_set
        self._validate_provider(request.provider if "provider" in fields else None)
        async with self._uow_factory() as uow:
            character = await uow.characters.get_owned(
                character_id,
                user_id,
                for_update=True,
            )
            if character is None:
                raise self._not_found()
            current = await uow.character_versions.get_version(
                character.id,
                character.current_version,
            )
            if current is None:
                raise RuntimeError("Character current version is missing.")

            for field in fields & self._root_fields:
                setattr(character, field, getattr(request, field))

            version = current
            if fields & self._version_fields:
                payload = {
                    field: (
                        getattr(request, field)
                        if field in fields
                        else getattr(current, field)
                    )
                    for field in self._version_fields
                }
                if not payload["name"]:
                    raise ValidationException("Character name cannot be empty.")
                character.current_version += 1
                version = CharacterVersion(
                    id=uuid4(),
                    character_id=character.id,
                    version=character.current_version,
                    version_metadata=dict(current.version_metadata),
                    **payload,
                )
                await uow.character_versions.add(version)

            await uow.flush()
            response = self._response(character, version)
            await uow.commit()
            return response

    async def archive(self, user_id: UUID, character_id: UUID) -> None:
        async with self._uow_factory() as uow:
            character = await uow.characters.get_owned(
                character_id,
                user_id,
                for_update=True,
            )
            if character is None:
                raise self._not_found()
            character.archived_at = datetime.now(UTC)
            await uow.commit()

    def _response(
        self,
        character: Character,
        version: CharacterVersion,
    ) -> CharacterResponse:
        return CharacterResponse(
            id=character.id,
            current_version=character.current_version,
            name=version.name,
            summary=version.summary,
            personality=version.personality,
            speaking_style=version.speaking_style,
            scenario=version.scenario,
            greeting=version.greeting,
            system_instructions=version.system_instructions,
            avatar_url=character.avatar_url,
            provider=character.provider,
            model=character.model,
            temperature=character.temperature,
            max_tokens=character.max_tokens,
            metadata=dict(character.character_metadata),
            created_at=character.created_at,
            updated_at=character.updated_at,
        )

    def _validate_provider(self, provider: str | None) -> None:
        if provider is None:
            return
        try:
            LLMProviderName(provider)
        except ValueError as exc:
            raise ValidationException(f"Unsupported provider: {provider}") from exc

    def _require_version(
        self,
        versions: dict[UUID, CharacterVersion],
        character_id: UUID,
    ) -> CharacterVersion:
        try:
            return versions[character_id]
        except KeyError as exc:
            raise RuntimeError("Character current version is missing.") from exc

    def _not_found(self) -> NotFoundException:
        return NotFoundException(
            "Character was not found.",
            code=ErrorCode.CHARACTER_NOT_FOUND,
        )
