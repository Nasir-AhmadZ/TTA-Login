import os
import hashlib
import binascii
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from Login.configurations import collection


def _ensure_indexes() -> None: # ensures unique indexes on username and email fields
    try:
        collection.create_index("username", unique=True)
        collection.create_index("email", unique=True)
    except Exception:
        # ignore index creation errors at import time
        pass


_ensure_indexes()


class UserModel:

    @staticmethod
    def _hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]: # hashes password with optional salt
        if salt is None:
            salt = os.urandom(16) # generates new salt if not provided
        # hashes password using PBKDF2-HMAC-SHA256 key derivation
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000) # sha256 = algorithm, utf-8 = encoding, salt = randomly generated 16 bytes, 100_000 = iterations 
        return {"salt": binascii.hexlify(salt).decode("ascii"), "password_hash": binascii.hexlify(pwd_hash).decode("ascii")}

    @staticmethod
    def _verify_password(stored_hash: str, stored_salt: str, provided_password: str) -> bool:
        try:
            salt = binascii.unhexlify(stored_salt.encode("ascii")) # convert hex back to bytes
        except Exception:
            return False
        pwd_hash = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100_000) # hashes provided password
        return binascii.hexlify(pwd_hash).decode("ascii") == stored_hash # compares hashes and returns True/False

    @staticmethod
    def _serialize(doc: Dict[str, Any], hide_sensitive: bool = True) -> Dict[str, Any]: # serializes user document
        if not doc:
            return None
        out = {k: v for k, v in doc.items()} # copy all fields
        _id = out.pop("_id", None) # remove _id field
        out["id"] = str(_id) if _id is not None else None # convert MongoDB ObjectId to string
        if hide_sensitive:
            out.pop("password_hash", None) # removes sensitive fields
            out.pop("salt", None)
        return out

    @classmethod
    def create_user(cls, username: str, password: str, email: str) -> str: # input username, password, email and creates user
        
        creds = cls._hash_password(password) # _hash_password returns dict with hash and salt
        doc = {
            "username": username,
            "email": email,
            "password_hash": creds["password_hash"],
            "salt": creds["salt"],
            "created_at": datetime.now(timezone.utc),
        }
        try:
            result = collection.insert_one(doc) # create user in database
            return str(result.inserted_id) # return user id as string
        except DuplicateKeyError as ex:
            # Determine which key caused the conflict
            if collection.find_one({"username": username}):
                raise ValueError("username_exists")
            if collection.find_one({"email": email}):
                raise ValueError("email_exists")

    @classmethod
    def find_by_username(cls, username: str) -> Optional[Dict[str, Any]]: # find user by username
        doc = collection.find_one({"username": username})
        return cls._serialize(doc, hide_sensitive=False) if doc else None

    @classmethod
    def find_by_email(cls, email: str) -> Optional[Dict[str, Any]]: # find user by email
        doc = collection.find_one({"email": email})
        return cls._serialize(doc, hide_sensitive=False) if doc else None

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional[Dict[str, Any]]: # return defined user if authentication successful
        doc = collection.find_one({"username": username}) # fetch user document
        if not doc:
            return None
        if cls._verify_password(doc.get("password_hash", ""), doc.get("salt", ""), password): # verifies password by comparing hashes
            return cls._serialize(doc, hide_sensitive=True) # removing sensitive fields and returns user data
        return None



