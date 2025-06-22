import click
from app.db.sync import SyncSessionLocal
from app.services.auth_service import AuthService
from app.core.security import get_password_hash

@click.group()
def cli():
    pass

@cli.command()
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def create_superuser(username: str, password: str):
    with SyncSessionLocal() as db:
        pwd_hash = get_password_hash(password)
        AuthService.create_user(
            db=db,
            username=username,
            password_hash=pwd_hash,
            is_superuser=True
        )
    click.echo(f"Суперпользователь '{username}' создан.")

if __name__ == "__main__":
    cli()