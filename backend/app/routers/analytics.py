from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from ..auth import require_roles
from ..db import get_db
from ..models import DatasetRequest, Episode, Quality, RequestStatus, Role, StatusHistory, User
from ..schemas import AnalyticsOut
router = APIRouter()

@router.get("", response_model=AnalyticsOut)
def analytics(start: datetime = Query(...), end: datetime = Query(...), db: Session = Depends(get_db), user: User = Depends(require_roles(Role.operator, Role.admin))):
    per_day = select(func.date(Episode.recorded_at).label("day"), Episode.robot_id, func.count().label("count")).where(Episode.recorded_at >= start, Episode.recorded_at < end).group_by(func.date(Episode.recorded_at), Episode.robot_id).order_by(func.date(Episode.recorded_at), Episode.robot_id)
    rows = db.execute(per_day).all()
    by_status = select(DatasetRequest.status, func.count().label("count")).where(DatasetRequest.created_at >= start, DatasetRequest.created_at < end).group_by(DatasetRequest.status)
    status_rows = db.execute(by_status).all()
    top = select(Episode.task_name, func.count().label("count")).where(Episode.recorded_at >= start, Episode.recorded_at < end, Episode.quality == Quality.good).group_by(Episode.task_name).order_by(func.count().desc()).limit(5)
    top_rows = db.execute(top).all()

    # PostgreSQL does the percentile calculation; no episode/request dataset is loaded into Python.
    median_sql = text("""
      SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (d.delivered_at - d.submitted_at)))
      FROM (
        SELECT sh.request_id,
          MIN(sh.changed_at) FILTER (WHERE sh.to_status = 'submitted') AS submitted_at,
          MIN(sh.changed_at) FILTER (WHERE sh.to_status = 'delivered') AS delivered_at
        FROM status_history sh
        GROUP BY sh.request_id
      ) d
      WHERE d.submitted_at IS NOT NULL AND d.delivered_at IS NOT NULL
        AND d.submitted_at >= :start AND d.delivered_at < :end
    """)
    median = db.execute(median_sql, {"start": start, "end": end}).scalar()
    return {
      "episodes_per_day_robot": [{"day": str(r.day), "robot_id": r.robot_id, "count": r.count} for r in rows],
      "requests_by_status": [{"status": r.status.value, "count": r.count} for r in status_rows],
      "median_submitted_to_delivered_seconds": float(median) if median is not None else None,
      "top_good_tasks": [{"task_name": r.task_name, "count": r.count} for r in top_rows],
    }
