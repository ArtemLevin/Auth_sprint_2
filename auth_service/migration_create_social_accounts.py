import sqlalchemy as sa

from alembic import op


def upgrade() -> None:
    op.create_table(
        "social_accounts",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_user_id", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_social_accounts_user",
        "social_accounts",
        ["user_id"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("ix_social_accounts_user", table_name="social_accounts")
    op.drop_table("social_accounts")