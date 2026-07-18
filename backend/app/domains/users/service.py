from uuid import UUID

from app.common.exceptions import NotFoundException
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.users.schemas import UserResponse


class UserService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_user(self, user_id: UUID) -> UserResponse:
        """Return a user by identifier without exposing the ORM entity."""
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if user is None:
                raise NotFoundException("User not found.")
            return UserResponse.model_validate(user)
