import sqlalchemy as sa

from alembic import op


def upgrade() -> None:
    op.execute("ALTER TABLE login_history RENAME TO login_history_old;")

    op.execute("""
        CREATE TABLE login_history (
            login_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            id         UUID         NOT NULL,
            user_id    UUID         NOT NULL,
            ip_address VARCHAR(50),
            user_agent VARCHAR(255),

            -- В состав PK обязательно включаем login_at
            CONSTRAINT pk_login_history PRIMARY KEY (login_at, id),
            CONSTRAINT fk_login_history_user FOREIGN KEY (user_id)
              REFERENCES users(id) ON DELETE CASCADE
        ) PARTITION BY RANGE (login_at);
    """)

    op.execute("""
        CREATE TABLE login_history_2025_06
            PARTITION OF login_history
            FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
    """)
    op.execute("""
        CREATE TABLE login_history_2025_07
            PARTITION OF login_history
            FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
    """)

    op.execute("""
        INSERT INTO login_history (login_at, id, user_id, ip_address, user_agent)
        SELECT login_at, id, user_id, ip_address, user_agent
          FROM login_history_old;
    """)

    op.execute("DROP TABLE login_history_old;")

    op.create_index("ix_login_history_login_at", "login_history", ["login_at"])
    op.create_index("ix_login_history_user_id", "login_history", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_login_history_user_id", table_name="login_history")
    op.drop_index("ix_login_history_login_at", table_name="login_history")
    op.execute("DROP TABLE IF EXISTS login_history;")
    op.execute("ALTER TABLE login_history_old RENAME TO login_history;")