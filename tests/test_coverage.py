
import sys
import pathlib

# Ensure project root is on sys.path for imports
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
from types import SimpleNamespace
from fastapi.testclient import TestClient
import pytest

from Login import main as app_module


@pytest.fixture(autouse=True)
def disable_rabbitmq(monkeypatch):
	class DummyPublisher:
		def connect(self):
			return False
		def publish_user_registration(self, *a, **k):
			return True
		def publish_user_login(self, *a, **k):
			return True
		def publish_user_deletion(self, *a, **k):
			return True
		def publish_user_logout(self, *a, **k):
			return True

	monkeypatch.setattr(app_module, "get_rabbitmq_publisher", lambda: DummyPublisher())


@pytest.fixture(autouse=True)
def use_test_db(monkeypatch):
	class FakeResult(SimpleNamespace):
		pass

	class FakeCollection:
		def __init__(self):
			self._data = {}

		def create_index(self, *a, **k):
			return None

		def find(self, *a, **k):
			return list(self._data.values())

		def find_one(self, q, *args, **kwargs):
			if not q:
				return None
			username = q.get("username")
			# handle queries like {"username": {"$ne": "bob"}}
			if isinstance(username, dict):
				if "$ne" in username:
					ne_val = username["$ne"]
					# if email also provided, find a doc with that email and username != ne_val
					email = q.get("email")
					if email:
						for v in self._data.values():
							if v.get("email") == email and v.get("username") != ne_val:
								return v
						return None
				# other operators not supported in fake collection
				return None
			if username:
				return self._data.get(username)
			email = q.get("email")
			if email:
				for v in self._data.values():
					if v.get("email") == email:
						return v
			return None

		def insert_one(self, doc):
			doc_copy = doc.copy()
			doc_copy["_id"] = doc_copy.get("username")
			self._data[doc_copy["username"]] = doc_copy
			return FakeResult(inserted_id=doc_copy["_id"])

		def update_one(self, q, u):
			username = q.get("username")
			if username in self._data:
				for k, v in u.get("$set", {}).items():
					self._data[username][k] = v
				return FakeResult(modified_count=1)
			return FakeResult(modified_count=0)

		def delete_one(self, q):
			username = q.get("username")
			if username in self._data:
				del self._data[username]
				return FakeResult(deleted_count=1)
			return FakeResult(deleted_count=0)

		@property
		def database(self):
			return self

		def get_collection(self, name):
			return self

	fake_col = FakeCollection()
	# seed a user for GET
	fake_col.insert_one({"username": "alice", "email": "alice@example.com", "password_hash": "h", "salt": "s"})

	# patch module-level collection used by main, configurations, and models
	monkeypatch.setattr(app_module, "collection", fake_col)
	import Login.configurations as conf
	monkeypatch.setattr(conf, "collection", fake_col)
	import Login.models as models
	monkeypatch.setattr(models, "collection", fake_col)
	yield


@pytest.fixture
def client():
	from fastapi.testclient import TestClient
	with TestClient(app_module.app) as c:
		yield c


def test_get_users(client):
	r = client.get("/users")
	assert r.status_code == 200
	data = r.json()
	assert isinstance(data, list)


def test_get_user(client):
	r = client.get("/users/alice")
	assert r.status_code == 200
	data = r.json()
	assert data["username"] == "alice"


def test_register_login_update_delete_logout(client):
	# register bob
	reg = {"username": "bob", "password": "pass123", "email": "bob@example.com"}
	r = client.post("/register", json=reg)
	assert r.status_code == 200
	assert "id" in r.json()

	# login bob
	login = {"username": "bob", "password": "pass123", "email": "bob@example.com"}
	r = client.post("/login", json=login)
	assert r.status_code == 200
	token = r.json().get("access_token")
	assert token is not None

	# update email
	update = {"email": "bob2@example.com"}
	r = client.put("/users/bob", json=update)
	assert r.status_code == 200
	assert r.json().get("email") == "bob2@example.com"

	# logout
	r = client.post("/logout", json={"username": "bob", "token": token})
	assert r.status_code == 200

	# delete
	r = client.delete("/users/bob")
	assert r.status_code == 200

