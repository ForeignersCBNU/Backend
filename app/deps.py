from fastapi import Header, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import select
from app.auth.security import SECRET, ALG
from app.db.session import SessionLocal
from app.db.models import User

def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1].strip()

async def get_current_user(authorization: str | None = Header(default=None)) -> User:
    token = _extract_bearer_token(authorization)
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALG])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async with SessionLocal() as s:
        user = (await s.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
