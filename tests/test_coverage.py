
import json


def test_get_users(client):
    r = client.get("/users")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_get_user(client):
    # seeded by conftest
    r = client.get("/users/guest")
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "guest"


def test_register_user(client):
    reg = {"username": "guest", "password": "pass123", "email": "bob@example.com"}
    r = client.post("/register", json=reg)
    assert r.status_code == 200
    assert "id" in r.json()


def test_login_user(client):
    # ensure user exists
    reg = {"username": "bob", "password": "pass123", "email": "bob@example.com"}
    client.post("/register", json=reg)

    login = {"username": "bob", "password": "pass123", "email": "bob@example.com"}
    r = client.post("/login", json=login)
    assert r.status_code == 200
    token = r.json().get("access_token")
    assert token is not None


def test_update_user_email(client):
    reg = {"username": "bob", "password": "pass123", "email": "bob@example.com"}
    client.post("/register", json=reg)

    update = {"email": "bob2@example.com"}
    r = client.put("/users/bob", json=update)
    assert r.status_code == 200
    assert r.json().get("email") == "bob2@example.com"


def test_logout_user(client):
    reg = {"username": "bob", "password": "pass123", "email": "bob@example.com"}
    client.post("/register", json=reg)
    r = client.post("/login", json={"username": "bob", "password": "pass123", "email": "bob@example.com"})
    token = r.json().get("access_token")

    r2 = client.post("/logout", json={"username": "bob" })
    assert r2.status_code == 200


def test_delete_user(client):
    reg = {"username": "bob", "password": "pass123", "email": "bob@example.com"}
    client.post("/register", json=reg)
    r = client.delete("/users/bob")
    assert r.status_code == 200
	# update email
