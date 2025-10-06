# Login/schemas.py
from pydantic import BaseModel, EmailStr, constr, conint

class User(BaseModel):
    user_id:int
    username:constr(min_length=2,max_length=50)
    password:constr(min_length=8,max_length=8)
    email:EmailStr
    