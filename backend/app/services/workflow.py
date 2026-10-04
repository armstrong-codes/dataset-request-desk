from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..models import Assignment, DatasetRequest, RequestStatus, StatusHistory

ALLOWED = {
    RequestStatus.submitted: {RequestStatus.in_progress},
    RequestStatus.in_progress: {RequestStatus.delivered},
    RequestStatus.delivered: {RequestStatus.accepted, RequestStatus.rejected},
    RequestStatus.rejected: {RequestStatus.in_progress},
    RequestStatus.accepted: set(),
}

def change_status(db: Session, request: DatasetRequest, new_status: RequestStatus, actor_id: int):
    if new_status not in ALLOWED[request.status]:
        raise HTTPException(409, f"Invalid transition: {request.status.value} -> {new_status.value}")
    if new_status == RequestStatus.delivered:
        count = db.scalar(select(func.count()).select_from(Assignment).where(Assignment.request_id == request.id))
        if count < request.episodes_requested:
            raise HTTPException(409, "Cannot deliver before enough episodes are assigned")
    old = request.status
    request.status = new_status
    db.add(StatusHistory(request_id=request.id, from_status=old, to_status=new_status, changed_by=actor_id))
    db.commit()
    db.refresh(request)
    return request
