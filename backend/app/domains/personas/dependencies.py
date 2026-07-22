from typing import Annotated

from fastapi import Depends

from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.personas.service import PersonaService


def get_persona_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> PersonaService:
    return PersonaService(uow_factory)
