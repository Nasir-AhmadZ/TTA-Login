# Login/schemas.py
from pydantic import BaseModel, EmailStr, constr, conint

class UserLogin(BaseModel):
    username:constr(min_length=2,max_length=50)
    password:constr(max_length=8)
    email:EmailStr
    
class UserRegister(BaseModel):
    username:constr(min_length=2,max_length=50)
    password:constr(max_length=8)
    email:EmailStr
