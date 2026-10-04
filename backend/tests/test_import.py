from pathlib import Path
from app.services.importer import import_csv

def test_import_is_idempotent(db):
    path=Path(__file__).resolve().parents[2] / 'candidate-pack' / 'seed' / 'episodes.csv'
    if not path.exists():
        return
    first=import_csv(db,str(path)); second=import_csv(db,str(path))
    assert first['imported']>0
    assert second['imported']==0
    assert second['reasons'].get('duplicate_episode_id',0)>0
