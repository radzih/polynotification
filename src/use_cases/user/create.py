from datetime import datetime

from src.domain.entities.user import UserDTO
from src.domain.protocols.repositories.user import UserRepository


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def __call__(self, user_id: int, username: str | None, full_name: str) -> UserDTO:
        # Pass dummy datetime for DTO creation before DB insertion
        # The repo will return the actual DB-generated timestamp
        user_dto = UserDTO(
            id=user_id,
            username=username,
            full_name=full_name,
            created_at=datetime.now() 
        )
        return await self.user_repo.create_user(user_dto)
