from auth_service.app.models.role import Role
from auth_service.app.models.user import User
from auth_service.app.models.user_role import UserRole
from auth_service.app.db.session import AsyncDBSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update, insert
from auth_service.app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from uuid import UUID as PyUUID
from typing import Optional, List


class RoleService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_role(self, role_data: RoleCreate) -> Role:
        existing_role = await self.db_session.execute(
            select(Role).where(Role.name == role_data.name)
        )
        if existing_role.scalar_one_or_none():
            raise ValueError(f"Role with name '{role_data.name}' already exists.")

        role = Role(**role_data.model_dump())
        self.db_session.add(role)
        await self.db_session.commit()
        await self.db_session.refresh(role)
        return role

    async def get_all_roles(self) -> list[Role]:
        result = await self.db_session.execute(select(Role))
        return result.scalars().all()

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        return await self.db_session.get(Role, PyUUID(role_id))

    async def update_role(
        self, role_id: str, role_update: RoleUpdate
    ) -> Optional[Role]:
        role = await self.db_session.get(Role, PyUUID(role_id))
        if not role:
            return None
        for field, value in role_update.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        await self.db_session.commit()
        await self.db_session.refresh(role)
        return role

    async def delete_role(self, role_id: str) -> bool:
        result = await self.db_session.execute(
            delete(Role).where(Role.id == PyUUID(role_id))
        )
        await self.db_session.commit()
        return result.rowcount > 0

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        user_exists = await self.db_session.get(User, PyUUID(user_id))
        role_exists = await self.db_session.get(Role, PyUUID(role_id))
        if not user_exists or not role_exists:
            return False

        existing_assignment = await self.db_session.execute(
            select(UserRole).where(
                UserRole.user_id == PyUUID(user_id), UserRole.role_id == PyUUID(role_id)
            )
        )
        if existing_assignment.scalar_one_or_none():
            return False

        user_role = UserRole(user_id=PyUUID(user_id), role_id=PyUUID(role_id))
        self.db_session.add(user_role)
        await self.db_session.commit()
        return True

    async def revoke_role_from_user(self, user_id: str, role_id: str) -> bool:
        result = await self.db_session.execute(
            delete(UserRole).where(
                UserRole.user_id == PyUUID(user_id), UserRole.role_id == PyUUID(role_id)
            )
        )
        await self.db_session.commit()
        return result.rowcount > 0

    async def get_user_permissions(self, user_id: str) -> List[str]:
        result = await self.db_session.execute(
            select(Role.permissions)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == PyUUID(user_id))
        )
        all_permissions = set()
        for row in result.scalars().all():
            all_permissions.update(row)
        return list(all_permissions)
