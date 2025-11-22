from pydantic import BaseModel, EmailStr, constr
from typing import Optional


class UserLogin(BaseModel): # schema for user login
    username: constr(min_length=2, max_length=50)
    password: constr(max_length=12)
    email: EmailStr


class UserRegister(BaseModel): # schema for user registration
    username: constr(min_length=2, max_length=50)
    password: constr(max_length=12)
    email: EmailStr


class UserUpdate(BaseModel): # schema for updating user info
    password: Optional[constr(max_length=12)] = None
    email: Optional[EmailStr] = None
