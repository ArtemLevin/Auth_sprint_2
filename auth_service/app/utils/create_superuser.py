import asyncio
from app.db.session import async_session
from app.models import User
from app.core.security import hash_password
import typer

app = typer.Typer()

@app.command()
def create_superuser(login: str, password: str):
    async def main():
        hashed = hash_password(password)
        async with async_session.begin() as session:
            user = User(login=login, password_hash=hashed, is_superuser=True)
            session.add(user)
            await session.commit()
            print(f"Superuser {login} created")
    asyncio.run(main())