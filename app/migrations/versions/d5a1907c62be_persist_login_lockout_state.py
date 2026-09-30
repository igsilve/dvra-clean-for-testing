"""Persist login lockout state on the user row

The in-process throttle in apis.auth.utils.lockout still runs, but it dies
with the worker and is not shared between them, so a restart or a second
worker multiplies the effective threshold. These columns make the count
survive both.

Revision ID: d5a1907c62be
Revises: c3e88a1d5f47
Create Date: 2026-09-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5a1907c62be"
down_revision: Union[str, None] = "c3e88a1d5f47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_logins", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_logins")
