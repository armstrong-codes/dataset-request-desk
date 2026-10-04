import json, os
from sqlalchemy import select
from .db import SessionLocal
from .models import User, Role
from .auth import hash_password

def main():
    path = "/seed/users.json"
    if not os.path.exists(path):
        return
    db = SessionLocal()
    try:
        for item in json.load(open(path)):
            existing = db.scalar(select(User).where(User.email == item["email"]))
            if existing: continue
            db.add(User(email=item["email"], password_hash=hash_password(item["password"]), name=item["name"], role=Role(item["role"]), organisation=item.get("organisation")))
        db.commit()
    finally:
        db.close()
if __name__ == "__main__": main()
