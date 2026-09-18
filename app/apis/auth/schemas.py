from typing import Union

from pydantic import BaseModel
from pydantic import constr


DisplayName = constr(strip_whitespace=True, min_length=1, max_length=64, regex=r"^[A-Za-z0-9 .,'-]+$")
Username = constr(strip_whitespace=True, min_length=3, max_length=32, regex=r"^[A-Za-z0-9_.-]+$")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: Username
    phone_number: str
    first_name: Union[DisplayName, None] = None
    last_name: Union[DisplayName, None] = None
    role: Union[str, None] = None


class UserRead(BaseModel):
    username: Username
    phone_number: str
    first_name: Union[DisplayName, None] = None
    last_name: Union[DisplayName, None] = None
    role: str


class UserUpdate(BaseModel):
    username: Username
    first_name: Union[DisplayName, None] = None
    last_name: Union[DisplayName, None] = None
    phone_number: Union[str, None] = None


class UserCreate(BaseModel):
    username: Username
    password: str
    phone_number: str
    first_name: Union[DisplayName, None] = None
    last_name: Union[DisplayName, None] = None


class NewPasswordData(BaseModel):
    username: str
    reset_password_code: str
    new_password: str
