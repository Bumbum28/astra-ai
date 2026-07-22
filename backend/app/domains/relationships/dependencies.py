from typing import Annotated

from fastapi import Depends

from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.relationships.service import RelationshipService


def get_relationship_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> RelationshipService:
    return RelationshipService(uow_factory)
