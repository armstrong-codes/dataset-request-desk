from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..auth import get_current_user, require_roles
from ..db import get_db
from ..models import Assignment, DatasetRequest, Episode, Quality, RequestStatus, Role, User, StatusHistory
from ..schemas import AssignmentCreate, RequestCreate, RequestOut, StatusChange
from ..services.workflow import change_status
router = APIRouter()

@router.post("", response_model=RequestOut, status_code=201)
def create_request(body: RequestCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.client))):
    # Admin is allowed to act on behalf of a client for convenience.
    client_id = user.id
    item = DatasetRequest(client_id=client_id, task_name=" ".join(body.task_name.lower().split()), episodes_requested=body.episodes_requested, deadline=body.deadline, notes=body.notes)
    db.add(item); db.flush(); db.add(StatusHistory(request_id=item.id, from_status=None, to_status=RequestStatus.submitted, changed_by=user.id)); db.commit(); db.refresh(item)
    return item

@router.get("", response_model=list[RequestOut])
def list_requests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(DatasetRequest).order_by(DatasetRequest.created_at.desc())
    if user.role == Role.client:
        stmt = stmt.where(DatasetRequest.client_id == user.id)
    return list(db.scalars(stmt))

@router.post("/{request_id}/status", response_model=RequestOut)
def set_status(request_id: int, body: StatusChange, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(DatasetRequest, request_id)
    if not item: raise HTTPException(404, "Request not found")
    if user.role == Role.client:
        if item.client_id != user.id or body.status not in {RequestStatus.accepted, RequestStatus.rejected}:
            raise HTTPException(403, "Clients can only accept/reject their own delivered requests")
    elif user.role not in {Role.operator, Role.admin}:
        raise HTTPException(403, "Forbidden")
    return change_status(db, item, body.status, user.id)

@router.post("/{request_id}/assign", status_code=201)
def assign_episode(request_id: int, body: AssignmentCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.operator, Role.admin))):
    request = db.get(DatasetRequest, request_id)
    if not request: raise HTTPException(404, "Request not found")
    episode = db.get(Episode, body.episode_id)
    if not episode: raise HTTPException(404, "Episode not found")
    if episode.quality == Quality.bad: raise HTTPException(409, "Bad-quality episodes cannot be assigned")
    if db.scalar(select(Assignment).where(Assignment.episode_id == episode.episode_id)):
        raise HTTPException(409, "Episode is already assigned")
    if request.status not in {RequestStatus.submitted, RequestStatus.in_progress, RequestStatus.rejected}:
        raise HTTPException(409, "Cannot assign episodes to this request in its current status")
    db.add(Assignment(request_id=request.id, episode_id=episode.episode_id, assigned_by=user.id))
    db.commit()
    return {"request_id": request.id, "episode_id": episode.episode_id}

@router.get("/{request_id}/episodes")
def request_episodes(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    request = db.get(DatasetRequest, request_id)
    if not request: raise HTTPException(404, "Request not found")
    if user.role == Role.client and request.client_id != user.id: raise HTTPException(403, "Forbidden")
    stmt = select(Episode).join(Assignment, Assignment.episode_id == Episode.episode_id).where(Assignment.request_id == request_id)
    return list(db.scalars(stmt))
