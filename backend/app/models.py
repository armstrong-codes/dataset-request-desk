from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Role(str, Enum):
    client = "client"
    operator = "operator"
    admin = "admin"

class Quality(str, Enum):
    good = "good"
    usable = "usable"
    bad = "bad"

class RequestStatus(str, Enum):
    submitted = "submitted"
    in_progress = "in_progress"
    delivered = "delivered"
    accepted = "accepted"
    rejected = "rejected"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SAEnum(Role, name="role"), index=True)
    organisation: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class Episode(Base):
    __tablename__ = "episodes"
    episode_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    robot_id: Mapped[str] = mapped_column(String(64), index=True)
    task_name: Mapped[str] = mapped_column(String(255), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[float] = mapped_column()
    operator_name: Mapped[str] = mapped_column(String(255))
    quality: Mapped[Quality] = mapped_column(SAEnum(Quality, name="quality"), index=True)

class DatasetRequest(Base):
    __tablename__ = "dataset_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_name: Mapped[str] = mapped_column(String(255), index=True)
    episodes_requested: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[RequestStatus] = mapped_column(SAEnum(RequestStatus, name="request_status"), index=True, default=RequestStatus.submitted)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    client = relationship("User")

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("dataset_requests.id", ondelete="CASCADE"), index=True)
    episode_id: Mapped[str] = mapped_column(ForeignKey("episodes.episode_id", ondelete="RESTRICT"), unique=True, index=True)
    assigned_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("request_id", "episode_id", name="uq_request_episode"),)

class StatusHistory(Base):
    __tablename__ = "status_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("dataset_requests.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[RequestStatus | None] = mapped_column(SAEnum(RequestStatus, name="history_from_status"))
    to_status: Mapped[RequestStatus] = mapped_column(SAEnum(RequestStatus, name="history_to_status"))
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

Index("ix_episodes_recorded_robot", Episode.recorded_at, Episode.robot_id)
