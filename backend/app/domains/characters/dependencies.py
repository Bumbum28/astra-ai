from typing import Annotated

from fastapi import Depends

from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.characters.service import CharacterService


def get_character_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> CharacterService:
    return CharacterService(uow_factory)
