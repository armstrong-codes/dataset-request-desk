from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..auth import get_current_user, hash_password, require_roles
from ..db import get_db
from ..models import Assignment, DatasetRequest, Episode, Role, User
from ..schemas import UserOut
router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    name: str
    role: Role
    organisation: str | None = None

class UserRoleChange(BaseModel):
    role: Role

@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    return list(db.scalars(select(User).order_by(User.id)))


@router.get("/stats")
def user_stats(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    total_users = db.scalar(select(func.count(User.id))) or 0
    active_users = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    inactive_users = total_users - active_users
    clients = db.scalar(select(func.count(User.id)).where(User.role == Role.client)) or 0
    operators = db.scalar(select(func.count(User.id)).where(User.role == Role.operator)) or 0
    admins = db.scalar(select(func.count(User.id)).where(User.role == Role.admin)) or 0
    total_requests = db.scalar(select(func.count(DatasetRequest.id))) or 0
    total_episodes = db.scalar(select(func.count(Episode.episode_id))) or 0
    total_assignments = db.scalar(select(func.count(Assignment.id))) or 0
    return {
        "users": {"total": total_users, "active": active_users, "inactive": inactive_users, "clients": clients, "operators": operators, "admins": admins},
        "requests": total_requests,
        "episodes": total_episodes,
        "assignments": total_assignments,
    }

@router.post("", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    if db.scalar(select(User).where(User.email == body.email.lower().strip())):
        raise HTTPException(409, "Email already exists")
    item=User(email=body.email.lower().strip(), password_hash=hash_password(body.password), name=body.name, role=body.role, organisation=body.organisation)
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    item=db.get(User,user_id)
    if not item: raise HTTPException(404,"User not found")
    if item.id == user.id: raise HTTPException(400,"You cannot deactivate yourself")
    item.is_active=False; db.commit(); db.refresh(item); return item


@router.patch("/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(404, "User not found")
    item.is_active = True
    db.commit()
    db.refresh(item)
    return item

@router.patch("/{user_id}/role", response_model=UserOut)
def change_role(user_id: int, body: UserRoleChange, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.admin))):
    item=db.get(User,user_id)
    if not item: raise HTTPException(404,"User not found")
    item.role=body.role; db.commit(); db.refresh(item); return item
