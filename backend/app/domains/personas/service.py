from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.personas.model import Persona
from app.domains.personas.schemas import (
    PersonaCreateRequest,
    PersonaListResponse,
    PersonaResponse,
    PersonaUpdateRequest,
)


class PersonaService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self, user_id: UUID, request: PersonaCreateRequest
    ) -> PersonaResponse:
        """Create a persona representing how the user appears in a conversation."""
        persona = Persona(
            id=uuid4(),
            user_id=user_id,
            name=request.name,
            description=request.description,
            instructions=request.instructions,
            is_default=request.is_default,
            persona_attributes=request.attributes,
        )
        async with self._uow_factory() as uow:
            if request.is_default:
                await uow.personas.clear_default(user_id)
            await uow.personas.add(persona)
            await uow.flush()
            response = PersonaResponse.model_validate(persona)
            await uow.commit()
            return response

    async def list_for_user(self, user_id: UUID) -> PersonaListResponse:
        """List personas owned by the current user."""
        async with self._uow_factory() as uow:
            items = await uow.personas.list_for_user(user_id)
        return PersonaListResponse(
            items=[PersonaResponse.model_validate(item) for item in items]
        )

    async def update(
        self, user_id: UUID, persona_id: UUID, request: PersonaUpdateRequest
    ) -> PersonaResponse:
        """Update a persona and keep the default-persona invariant."""
        async with self._uow_factory() as uow:
            persona = await uow.personas.get_owned(persona_id, user_id, for_update=True)
            if persona is None:
                raise self._not_found()
            if request.is_default is True:
                await uow.personas.clear_default(user_id, except_id=persona_id)
            for field in request.model_fields_set:
                if field == "attributes":
                    persona.persona_attributes = request.attributes or {}
                else:
                    setattr(persona, field, getattr(request, field))
            await uow.flush()
            response = PersonaResponse.model_validate(persona)
            await uow.commit()
            return response

    async def delete(self, user_id: UUID, persona_id: UUID) -> None:
        """Delete a persona after detaching it from conversations."""
        async with self._uow_factory() as uow:
            persona = await uow.personas.get_owned(persona_id, user_id, for_update=True)
            if persona is None:
                raise self._not_found()
            await uow.personas.delete(persona)
            await uow.commit()

    @staticmethod
    def _not_found() -> NotFoundException:
        return NotFoundException("Persona was not found.", code=ErrorCode.PERSONA_NOT_FOUND)
