"""Force a password change on system-seeded accounts

Adds users.must_change_password. Accounts created by the seeding routine hold
a password the system generated rather than one the holder chose, and must
replace it before the account can be used for anything else.

Existing rows default to false: they predate the flag and their passwords were
not issued by this mechanism, so locking them out would be a false positive.

Revision ID: c3e88a1d5f47
Revises: b7d41f0c9a12
Create Date: 2026-09-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e88a1d5f47"
down_revision: Union[str, None] = "b7d41f0c9a12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
