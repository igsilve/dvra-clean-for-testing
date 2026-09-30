"""Persist the reset-code attempt counter

Bounds the guesses that can be spent against a single reset code. Persisted
rather than held in process so the bound survives a restart and holds across
workers.

Revision ID: f7c2ab84d130
Revises: e91b4c73a208
Create Date: 2026-09-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7c2ab84d130"
down_revision: Union[str, None] = "e91b4c73a208"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "reset_password_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "reset_password_attempts")
