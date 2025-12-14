import sys
import pathlib

# ensure project root on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest
import mongomock
from fastapi.testclient import TestClient

import Login.main as main_mod
import Login.configurations as conf
import Login.models as models
import Login.rabbitmq_publisher as pubmod

# create a mongomock collection and inject into app modules
mongo_client = mongomock.MongoClient()
db = mongo_client["UserDB"]
fake_collection = db["userData"]

conf.collection = fake_collection
models.collection = fake_collection
main_mod.collection = fake_collection

# seed a test user so endpoint tests can find it
fake_collection.insert_one({
    "username": "guest",
    "email": "guest@example.com",
    "password_hash": "h",
    "salt": "s",
})


class RabbitMQPublish:
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


def _get_rabbit():
    return RabbitMQPublish()


# patch publisher factory so app code gets a dummy publisher
pubmod.get_rabbitmq_publisher = lambda: _get_rabbit()


@pytest.fixture
def client():
    with TestClient(main_mod.app) as c:
        yield c
