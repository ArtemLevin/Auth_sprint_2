import asyncio
from auth_service.app.db.session import AsyncDBSession
from auth_service.app.models import User
from auth_service.app.core.security import get_password_hash
import typer
from sqlalchemy.future import select

app = typer.Typer()


@app.command()
def create_superuser(login: str, password: str):
    async def main():
        hashed = get_password_hash(password)
        async with AsyncDBSession() as session:
            existing_user = await session.execute(
                select(User).where(User.login == login)
            )
            if existing_user.scalar_one_or_none():
                print(f"Error: User with login '{login}' already exists.")
                return

            user = User(login=login, password_hash=hashed, is_superuser=True)
            session.add(user)
            await session.commit()
            print(f"Superuser {login} created successfully!")

    asyncio.run(main())


if __name__ == "__main__":
    app()
