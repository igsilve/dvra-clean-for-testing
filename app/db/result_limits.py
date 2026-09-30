"""Centralized result-set size control for sensitive queries.

Every bounded read goes through `fetch_bounded` so the maximum row count,
the overflow response and the error message live in one place rather than
being re-derived per endpoint.
"""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Query

# Server-controlled ceiling. Never derived from request input.
MAX_ROWS = 500


def fetch_bounded(query: Query, max_rows: int = MAX_ROWS) -> List:
    """Return up to `max_rows` rows, or fail if the result set is larger.

    The limit is applied in SQL rather than by slicing in Python, so an
    oversized result is never materialized. One extra row is requested as a
    sentinel: getting it back proves the set exceeds the ceiling without
    needing a second COUNT query.
    """
    rows = query.limit(max_rows + 1).all()

    if len(rows) > max_rows:
        # Generic message: the caller learns the request was too broad, not
        # how many rows exist.
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Result set too large; narrow the query",
        )

    return rows
