from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List, Dict, Any

from Login.schemas import UserRegister, UserLogin, UserUpdate
from Login.models import UserModel
from Login.configurations import collection

app = FastAPI()


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return None
    out = {k: v for k, v in doc.items() if k not in ("password_hash", "salt")}
    _id = out.pop("_id", None)
    out["id"] = str(_id) if _id is not None else None
    return out


@app.get("/users", response_model=List[Dict[str, Any]])
def get_users():
    docs = collection.find({}, {"password_hash": 0, "salt": 0})
    return [_serialize(d) for d in docs]


@app.get("/users/{username}")
def get_user(username: str):
    doc = collection.find_one({"username": username}, {"password_hash": 0, "salt": 0})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _serialize(doc)


@app.post("/register")
def register(user: UserRegister):
    try:
        user_id = UserModel.create_user(user.username, user.password, user.email)
        return {"message": "User registered successfully", "id": user_id}
    except ValueError as e:
        if str(e) == "username_exists":
            raise HTTPException(status_code=400, detail="Username already exists")
        if str(e) == "email_exists":
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.put("/users/{username}")
def update_user(username: str, payload: UserUpdate):
    doc = collection.find_one({"username": username})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")

    update_fields: Dict[str, Any] = {}
    if payload.email:
        # ensure email not used by another user
        existing = collection.find_one({"email": payload.email, "username": {"$ne": username}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_fields["email"] = payload.email
    if payload.password:
        creds = UserModel._hash_password(payload.password)
        update_fields["password_hash"] = creds["password_hash"]
        update_fields["salt"] = creds["salt"]

    if not update_fields:
        return {"message": "No changes provided"}

    result = collection.update_one({"username": username}, {"$set": update_fields})
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Update failed")
    updated = collection.find_one({"username": username}, {"password_hash": 0, "salt": 0})
    return _serialize(updated)


@app.delete("/users/{username}")
def delete_user(username: str):
    result = collection.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@app.post("/login")
def login(user: UserLogin):
    auth = UserModel.authenticate(user.username, user.password)
    if not auth:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    token = f"token-{user.username}"
    return {"access_token": token, "token_type": "succeful", "user": auth}
