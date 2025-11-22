from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert

from src.domain.entities.user import UserDTO
from src.domain.protocols.repositories.user import UserRepository
from src.infrastructure.db.models.user import User


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user: UserDTO) -> UserDTO:
        # Note: We rely on server_default for created_at on insert if not provided,
        # but UserDTO expects it. For simple create, we can just return what we sent
        # or fetch the DB state.
        # The on_conflict_do_update will preserve created_at unless we explicitly update it.
        
        stmt = insert(User).values(
            id=user.id,
            username=user.username,
            full_name=user.full_name
        ).on_conflict_do_update(
            index_elements=[User.id],
            set_=dict(
                username=user.username,
                full_name=user.full_name
            )
        ).returning(User)

        result = await self.session.execute(stmt)
        db_user = result.scalar_one()
        await self.session.commit()
        
        return UserDTO(
            id=db_user.id,
            username=db_user.username,
            full_name=db_user.full_name,
            created_at=db_user.created_at
        )

    async def get_user(self, user_id: int) -> UserDTO | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
            
        return UserDTO(
            id=db_user.id,
            username=db_user.username,
            full_name=db_user.full_name,
            created_at=db_user.created_at
        )
