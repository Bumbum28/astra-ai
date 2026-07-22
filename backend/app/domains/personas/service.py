from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException, ValidationException
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.personas.model import Persona, PersonaVersion
from app.domains.personas.schemas import (
    PersonaCreateRequest,
    PersonaPageResponse,
    PersonaResponse,
    PersonaUpdateRequest,
)
from app.utils.cursors import CursorPosition, decode_cursor, encode_cursor


class PersonaService:
    _version_fields = {
        "name",
        "description",
        "pronouns",
        "background",
        "traits",
        "writing_style",
    }

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        user_id: UUID,
        request: PersonaCreateRequest,
    ) -> PersonaResponse:
        persona = Persona(
            id=uuid4(),
            user_id=user_id,
            current_version=1,
            persona_metadata=request.metadata,
        )
        version = PersonaVersion(
            id=uuid4(),
            persona_id=persona.id,
            version=1,
            name=request.name,
            description=request.description,
            pronouns=request.pronouns,
            background=request.background,
            traits=request.traits,
            writing_style=request.writing_style,
            version_metadata={},
        )
        async with self._uow_factory() as uow:
            await uow.personas.add(persona)
            await uow.persona_versions.add(version)
            await uow.flush()
            response = self._response(persona, version)
            await uow.commit()
            return response

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        cursor: str | None,
    ) -> PersonaPageResponse:
        page_size = min(limit, 100)
        decoded = decode_cursor(cursor) if cursor else None
        async with self._uow_factory() as uow:
            roots = list(
                await uow.personas.list_for_user(
                    user_id,
                    limit=page_size + 1,
                    cursor=decoded,
                )
            )
            has_more = len(roots) > page_size
            roots = roots[:page_size]
            versions = await uow.persona_versions.list_current(roots)

        versions_by_persona = {item.persona_id: item for item in versions}
        responses = [
            self._response(root, self._require_version(versions_by_persona, root.id))
            for root in roots
        ]
        next_cursor = None
        if has_more and roots:
            last = roots[-1]
            next_cursor = encode_cursor(
                CursorPosition(timestamp=last.updated_at, entity_id=last.id)
            )
        return PersonaPageResponse(items=responses, next_cursor=next_cursor)

    async def get(self, user_id: UUID, persona_id: UUID) -> PersonaResponse:
        async with self._uow_factory() as uow:
            persona = await uow.personas.get_owned(persona_id, user_id)
            if persona is None:
                raise self._not_found()
            version = await uow.persona_versions.get_version(
                persona.id,
                persona.current_version,
            )
            if version is None:
                raise RuntimeError("Persona current version is missing.")
            return self._response(persona, version)

    async def update(
        self,
        user_id: UUID,
        persona_id: UUID,
        request: PersonaUpdateRequest,
    ) -> PersonaResponse:
        fields = request.model_fields_set
        async with self._uow_factory() as uow:
            persona = await uow.personas.get_owned(
                persona_id,
                user_id,
                for_update=True,
            )
            if persona is None:
                raise self._not_found()
            current = await uow.persona_versions.get_version(
                persona.id,
                persona.current_version,
            )
            if current is None:
                raise RuntimeError("Persona current version is missing.")

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
                    raise ValidationException("Persona name cannot be empty.")
                persona.current_version += 1
                version = PersonaVersion(
                    id=uuid4(),
                    persona_id=persona.id,
                    version=persona.current_version,
                    version_metadata=dict(current.version_metadata),
                    **payload,
                )
                await uow.persona_versions.add(version)

            await uow.flush()
            response = self._response(persona, version)
            await uow.commit()
            return response

    async def archive(self, user_id: UUID, persona_id: UUID) -> None:
        async with self._uow_factory() as uow:
            persona = await uow.personas.get_owned(
                persona_id,
                user_id,
                for_update=True,
            )
            if persona is None:
                raise self._not_found()
            persona.archived_at = datetime.now(UTC)
            await uow.commit()

    def _response(self, persona: Persona, version: PersonaVersion) -> PersonaResponse:
        return PersonaResponse(
            id=persona.id,
            current_version=persona.current_version,
            name=version.name,
            description=version.description,
            pronouns=version.pronouns,
            background=version.background,
            traits=version.traits,
            writing_style=version.writing_style,
            metadata=dict(persona.persona_metadata),
            created_at=persona.created_at,
            updated_at=persona.updated_at,
        )

    def _require_version(
        self,
        versions: dict[UUID, PersonaVersion],
        persona_id: UUID,
    ) -> PersonaVersion:
        try:
            return versions[persona_id]
        except KeyError as exc:
            raise RuntimeError("Persona current version is missing.") from exc

    def _not_found(self) -> NotFoundException:
        return NotFoundException(
            "Persona was not found.",
            code=ErrorCode.PERSONA_NOT_FOUND,
        )
