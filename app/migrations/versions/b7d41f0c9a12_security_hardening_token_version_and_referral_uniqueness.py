"""Security hardening: per-user token version and referral coupon uniqueness

Revision ID: b7d41f0c9a12
Revises: f23331e973f8
Create Date: 2026-09-30 16:20:00.000000

Two schema changes backing security countermeasures:

- ``users.token_version`` is stamped into every issued JWT and compared on
  each request, so bumping it revokes tokens already handed out. This is how
  a password reset or role change takes effect immediately in a stateless
  token scheme with no server-side session to delete (T20).
- A partial unique index on ``discount_coupons`` enforces one referral coupon
  per account at the database level, closing the race that a read-then-write
  check in the handler cannot (T7382). The predicate keeps promotional
  coupons, which carry no referrer, outside the constraint.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d41f0c9a12"
down_revision: Union[str, None] = "f23331e973f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "uq_discount_coupons_referral_per_user"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index(
        INDEX_NAME,
        "discount_coupons",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("referrer_user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="discount_coupons")
    op.drop_column("users", "token_version")
