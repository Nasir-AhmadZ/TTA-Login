from fastapi import FastAPI, HTTPException, status
from .schemas import UserRegister, UserLogin
from configurations import collection

app = FastAPI()
users = {}

@app.get("/users")
def get_users():
    return users

@app.post("/register")
def register(user: UserRegister):
    if user.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
    # check if email already used
    if any(u["email"] == user.email for u in users.values()):
        raise HTTPException(status_code=400, detail="Email already registered")
    users[user.username] = {"password":user.password,"email":user.email}
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    if user.username not in users:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    if users[user.username]["password"] != user.password:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # simple fake token (for demo only)
    token = f"token-{user.username}"
    return {
        "access_token": token,
        "token_type": "fake",
        "email": users[user.username]["email"]
    }
