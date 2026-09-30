import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MenuItemCreate(BaseModel):
    # The text fields carry an explicit contract rather than accepting any
    # string of any length. Two reasons, and the second is the one that gets
    # forgotten: a bound is what stops a megabyte of markup being stored and
    # then handed to every consumer of this record, and `extra="forbid"`
    # means a field name this model does not declare is a 422 instead of
    # something a later mass-assignment might pick up.
    #
    # The values are still stored exactly as submitted -- escaping belongs to
    # the consumer that renders them, and encoding on the way in corrupts
    # the data for every consumer that does not render HTML.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    price: float = Field(gt=0, le=100_000)
    category: str = Field(min_length=1, max_length=60)
    image_url: Optional[str] = Field(default=None, max_length=2048)
    # The digest the caller expects the fetched bytes to have, and
    # optionally a signature over them. Both are supplied by the caller
    # rather than read back from the content, which is the point: the
    # caller states what it reviewed, and a host that serves something
    # else is caught instead of trusted.
    image_sha256: Optional[str] = Field(default=None, max_length=64)
    image_signature: Optional[str] = Field(default=None, max_length=1024)
    description: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _require_a_digest_alongside_a_url(self) -> "MenuItemCreate":
        if self.image_url and not self.image_sha256:
            raise ValueError(
                "image_sha256 is required when image_url is supplied"
            )
        if self.image_sha256 and not re.fullmatch(
            r"[0-9a-f]{64}", self.image_sha256
        ):
            raise ValueError("image_sha256 must be 64 lowercase hex characters")
        return self


class MenuItem(BaseModel):
    # Validated from ORM instances, including when nested in a response
    # envelope, which does not propagate from_attributes to its members.
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    category: str
    description: Optional[str] = None
    image_base64: Optional[str] = None
