import csv
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from ..models import Episode, Quality

KNOWN_ROBOTS = {"arm-01", "arm-02", "arm-03", "mobile-01", "humanoid-01"}
KNOWN_TASKS = {"pick cup", "wipe table", "fold towel", "stack blocks", "pour water", "open drawer", "place cup on shelf"}
DATE_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"]

def parse_datetime(value: str):
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None

def import_csv(db: Session, path: str):
    imported = skipped = 0
    reasons = {}
    def skip(reason):
        nonlocal skipped
        skipped += 1
        reasons[reason] = reasons.get(reason, 0) + 1
    seen = set()
    with Path(path).open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != ["episode_id", "robot_id", "task_name", "recorded_at", "duration_seconds", "operator_name", "quality"]:
            raise ValueError("Unexpected CSV header")
        for row in reader:
            if not row or all(not str(x).strip() for x in row):
                skip("blank_row"); continue
            if len(row) != 7:
                skip("malformed_row"); continue
            eid, robot, task, recorded, duration, operator, quality = [x.strip() for x in row]
            task = " ".join(task.lower().split())
            quality = quality.lower().strip()
            robot = robot.strip()
            if not eid: skip("missing_episode_id"); continue
            if eid in seen or db.get(Episode, eid): skip("duplicate_episode_id"); continue
            seen.add(eid)
            if robot not in KNOWN_ROBOTS: skip("unknown_robot"); continue
            if task not in KNOWN_TASKS: skip("unknown_task"); continue
            dt = parse_datetime(recorded)
            if not dt: skip("invalid_recorded_at"); continue
            try: dur = float(duration)
            except ValueError: skip("invalid_duration"); continue
            if dur < 0: skip("negative_duration"); continue
            if not operator: skip("missing_operator"); continue
            if quality not in {q.value for q in Quality}: skip("invalid_quality"); continue
            db.add(Episode(episode_id=eid, robot_id=robot, task_name=task, recorded_at=dt,
                           duration_seconds=dur, operator_name=operator, quality=Quality(quality)))
            imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped, "reasons": reasons}
