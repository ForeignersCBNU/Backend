import os
from datetime import datetime, timedelta
from jose import jwt
from passlib.hash import bcrypt
SECRET = os.getenv("JWT_SECRET", "change_me")
ALG = os.getenv("JWT_ALG", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN", "30"))
def hash_password(pw: str) -> str: return bcrypt.hash(pw)
def verify_password(pw: str, hashed: str) -> bool: return bcrypt.verify(pw, hashed)
def create_access_token(sub: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)
    return jwt.encode({"sub": sub, "exp": exp}, SECRET, algorithm=ALG)
