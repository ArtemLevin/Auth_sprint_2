import os, sys, asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.settings      import settings
from app.models.base   import Base
from app.db.session    import engine as async_db_engine

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle":"named"},
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    connectable = async_db_engine  # AsyncEngine
    async with connectable.connect() as conn:

        def do_sync_migrations(sync_conn):
            context.configure(
                connection=sync_conn,
                target_metadata=target_metadata,
            )
            with context.begin_transaction():
                context.run_migrations()

        await conn.run_sync(do_sync_migrations)

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())