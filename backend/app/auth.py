from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import base64, hashlib, hmac, os
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import Role, User

bearer = HTTPBearer()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()

def verify_password(password: str, hashed: str) -> bool:
    try:
        _, salt_b64, digest_b64 = hashed.split("$", 2)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user.id), "role": user.role.value, "exp": now + timedelta(minutes=settings.access_token_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive or missing")
    return user

def require_roles(*roles: Role):
    def dependency(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
