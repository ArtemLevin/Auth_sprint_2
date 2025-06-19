from auth_service.app.models.role import Role
from auth_service.app.db.session import async_session
from sqlalchemy.future import select

class RoleService:
    @staticmethod
    async def create_role(role_data):
        async with async_session.begin() as session:
            role = Role(**role_data.dict())
            session.add(role)
            await session.flush()
            return role