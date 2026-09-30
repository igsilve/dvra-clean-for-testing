from typing import Union

from password_policy import validate_password_policy
from pydantic import BaseModel, ConfigDict, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    phone_number: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    role: Union[str, None] = None


class UserRead(BaseModel):
    username: str
    phone_number: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    role: str


class UserUpdate(BaseModel):
    username: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    phone_number: Union[str, None] = None


class UserCreate(BaseModel):
    # Registration assigns the role server-side. Forbidding extras means a
    # body carrying role or is_admin is rejected outright instead of being
    # dropped silently and answered with 201, which reads like it worked.
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str
    phone_number: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None

    @field_validator("password")
    @classmethod
    def _enforce_password_policy(cls, value: str) -> str:
        # The same baseline that system accounts are held to; see
        # password_policy for why there is only one.
        return validate_password_policy(value)


class NewPasswordData(BaseModel):
    username: str
    reset_password_code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _enforce_password_policy(cls, value: str) -> str:
        return validate_password_policy(value, subject="new_password")
