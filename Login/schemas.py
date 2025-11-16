from pydantic import BaseModel, EmailStr, constr
from typing import Optional


class UserLogin(BaseModel):
    username: constr(min_length=2, max_length=50)
    password: constr(max_length=8)
    email: EmailStr


class UserRegister(BaseModel):
    username: constr(min_length=2, max_length=50)
    password: constr(max_length=8)
    email: EmailStr


class UserUpdate(BaseModel):
    password: Optional[constr(max_length=8)] = None
    email: Optional[EmailStr] = None
