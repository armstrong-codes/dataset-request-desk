from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import get_current_user, require_roles
from ..db import get_db
from ..models import Episode, Quality, Role, User
from ..schemas import EpisodeOut, ImportReport
from ..services.importer import import_csv
router = APIRouter()

@router.get("", response_model=list[EpisodeOut])
def list_episodes(task_name: str | None = None, quality: Quality | None = None, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.operator, Role.admin))):
    stmt = select(Episode).order_by(Episode.recorded_at.desc()).limit(min(limit, 500))
    if task_name: stmt = stmt.where(Episode.task_name == " ".join(task_name.lower().split()))
    if quality: stmt = stmt.where(Episode.quality == quality)
    return list(db.scalars(stmt))

@router.post("/import", response_model=ImportReport)
async def import_episodes(file: UploadFile = File(...), db: Session = Depends(require_roles(Role.operator, Role.admin))):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(400, "CSV file required")
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "wb") as f: f.write(await file.read())
        return import_csv(db, path)
    finally:
        try: os.remove(path)
        except OSError: pass
