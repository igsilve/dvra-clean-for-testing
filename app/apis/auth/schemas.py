import re
from typing import Union

from pydantic import BaseModel, Field, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str = Field(..., max_length=150)
    phone_number: str = Field(..., max_length=20)
    first_name: Union[str, None] = Field(None, max_length=100)
    last_name: Union[str, None] = Field(None, max_length=100)
    role: Union[str, None] = None


class UserRead(BaseModel):
    username: str = Field(..., max_length=150)
    phone_number: str = Field(..., max_length=20)
    first_name: Union[str, None] = Field(None, max_length=100)
    last_name: Union[str, None] = Field(None, max_length=100)
    role: str


class UserUpdate(BaseModel):
    username: str = Field(..., max_length=150)
    first_name: Union[str, None] = Field(None, max_length=100)
    last_name: Union[str, None] = Field(None, max_length=100)
    phone_number: Union[str, None] = Field(None, max_length=20)


class UserCreate(BaseModel):
    username: str = Field(..., max_length=150)
    password: str = Field(..., max_length=128)
    phone_number: str = Field(..., max_length=20)
    first_name: Union[str, None] = Field(None, max_length=100)
    last_name: Union[str, None] = Field(None, max_length=100)
    consent_to_data_processing: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        cleaned = re.sub(r"[^\d+]", "", v)
        if not re.match(r"^\+?[1-9]\d{7,14}$", cleaned):
            raise ValueError("Invalid phone number format; use E.164 (e.g. +12125551234)")
        return cleaned


class NewPasswordData(BaseModel):
    username: str = Field(..., max_length=150)
    reset_password_code: str = Field(..., max_length=64)
    new_password: str = Field(..., max_length=128)
