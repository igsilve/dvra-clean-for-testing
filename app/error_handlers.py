"""Explicit, minimal response schemas for error paths.

Error responses need shaping as much as success responses do. FastAPI's
default validation handler serializes the offending value back to the
caller, so a bad `password` field on /register would echo the submitted
password. These handlers project errors onto a fixed shape that names the
location and the error type but never the input.
"""

from typing import List

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class FieldError(BaseModel):
    loc: List[str]
    type: str


class ValidationErrorResponse(BaseModel):
    detail: str
    errors: List[FieldError]


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
        headers=getattr(exc, "headers", None),
    )


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Keep `loc` and `type` so a client can fix the request, and drop `msg`,
    # `input` and `ctx`, which carry the rejected value and internal detail.
    errors = [
        {
            "loc": [str(part) for part in error.get("loc", [])],
            "type": error.get("type", "invalid"),
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed", "errors": errors},
    )
