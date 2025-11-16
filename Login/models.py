import os
import hashlib
import binascii
from datetime import datetime
from typing import Optional, Dict, Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from configurations import collection


def _ensure_indexes() -> None:
    try:
        collection.create_index("username", unique=True)
        collection.create_index("email", unique=True)
    except Exception:
        # ignore index creation errors at import time
        pass


_ensure_indexes()


class UserModel:
    """Mongo-backed user helpers.

    Stored document shape:
      {
        "_id": ObjectId,
        "username": str,
        "email": str,
        "password_hash": str,  # hex
        "salt": str,           # hex
        "created_at": datetime
      }
    """

    @staticmethod
    def _hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        if salt is None:
            salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return {"salt": binascii.hexlify(salt).decode("ascii"), "password_hash": binascii.hexlify(pwd_hash).decode("ascii")}

    @staticmethod
    def _verify_password(stored_hash: str, stored_salt: str, provided_password: str) -> bool:
        try:
            salt = binascii.unhexlify(stored_salt.encode("ascii"))
        except Exception:
            return False
        pwd_hash = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100_000)
        return binascii.hexlify(pwd_hash).decode("ascii") == stored_hash

    @staticmethod
    def _serialize(doc: Dict[str, Any], hide_sensitive: bool = True) -> Dict[str, Any]:
        if not doc:
            return None
        out = {k: v for k, v in doc.items()}
        _id = out.pop("_id", None)
        out["id"] = str(_id) if _id is not None else None
        if hide_sensitive:
            out.pop("password_hash", None)
            out.pop("salt", None)
        return out

    @classmethod
    def create_user(cls, username: str, password: str, email: str) -> str:
        """Create a new user and return its id (string).

        Raises ValueError("username_exists") or ValueError("email_exists") on conflicts.
        """
        creds = cls._hash_password(password)
        doc = {
            "username": username,
            "email": email,
            "password_hash": creds["password_hash"],
            "salt": creds["salt"],
            "created_at": datetime.utcnow(),
        }
        try:
            result = collection.insert_one(doc)
            return str(result.inserted_id)
        except DuplicateKeyError as ex:
            # Determine which key caused the conflict
            if collection.find_one({"username": username}):
                raise ValueError("username_exists")
            if collection.find_one({"email": email}):
                raise ValueError("email_exists")
            raise

    @classmethod
    def find_by_username(cls, username: str) -> Optional[Dict[str, Any]]:
        doc = collection.find_one({"username": username})
        return cls._serialize(doc, hide_sensitive=False) if doc else None

    @classmethod
    def find_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        doc = collection.find_one({"email": email})
        return cls._serialize(doc, hide_sensitive=False) if doc else None

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional[Dict[str, Any]]:
        doc = collection.find_one({"username": username})
        if not doc:
            return None
        if cls._verify_password(doc.get("password_hash", ""), doc.get("salt", ""), password):
            return cls._serialize(doc, hide_sensitive=True)
        return None



