from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .models import Quality, RequestStatus, Role

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: Role
    organisation: str | None = None
    is_active: bool

class RequestCreate(BaseModel):
    task_name: str = Field(min_length=1, max_length=255)
    episodes_requested: int = Field(gt=0, le=1000000)
    deadline: datetime
    notes: str | None = None

class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    task_name: str
    episodes_requested: int
    deadline: datetime
    notes: str | None
    status: RequestStatus
    created_at: datetime

class StatusChange(BaseModel):
    status: RequestStatus

class AssignmentCreate(BaseModel):
    episode_id: str

class EpisodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    episode_id: str
    robot_id: str
    task_name: str
    recorded_at: datetime
    duration_seconds: float
    operator_name: str
    quality: Quality

class ImportReport(BaseModel):
    imported: int
    skipped: int
    reasons: dict[str, int]

class AnalyticsOut(BaseModel):
    episodes_per_day_robot: list[dict]
    requests_by_status: list[dict]
    median_submitted_to_delivered_seconds: float | None
    top_good_tasks: list[dict]
