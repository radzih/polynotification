from typing import Protocol

from src.domain.entities.user import UserDTO


class UserRepository(Protocol):
    async def create_user(self, user: UserDTO) -> UserDTO:
        ...
    
    async def get_user(self, user_id: int) -> UserDTO | None:
        ...

