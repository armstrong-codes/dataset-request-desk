from .conftest import token
from app.models import Episode, Quality

def test_client_only_sees_own_requests(client):
    t=token(client,'client@test.com','client')
    r=client.post('/requests',headers={'Authorization':f'Bearer {t}'},json={'task_name':'pick cup','episodes_requested':1,'deadline':'2026-10-10T10:00:00Z'})
    assert r.status_code==201
    assert len(client.get('/requests',headers={'Authorization':f'Bearer {t}'}).json())==1

def test_bad_episode_cannot_be_assigned(client, db):
    t=token(client,'client@test.com','client')
    req=client.post('/requests',headers={'Authorization':f'Bearer {t}'},json={'task_name':'pick cup','episodes_requested':1,'deadline':'2026-10-10T10:00:00Z'}).json()
    op=token(client,'ops@test.com','ops')
    db.add(Episode(episode_id='EP-X',robot_id='arm-01',task_name='pick cup',recorded_at=__import__('datetime').datetime.now(),duration_seconds=10,operator_name='X',quality=Quality.bad)); db.commit()
    r=client.post(f"/requests/{req['id']}/assign",headers={'Authorization':f'Bearer {op}'},json={'episode_id':'EP-X'})
    assert r.status_code==409

def test_cannot_deliver_without_enough_episodes(client):
    t=token(client,'client@test.com','client')
    req=client.post('/requests',headers={'Authorization':f'Bearer {t}'},json={'task_name':'pick cup','episodes_requested':2,'deadline':'2026-10-10T10:00:00Z'}).json()
    op=token(client,'ops@test.com','ops')
    client.post(f"/requests/{req['id']}/status",headers={'Authorization':f'Bearer {op}'},json={'status':'in_progress'})
    r=client.post(f"/requests/{req['id']}/status",headers={'Authorization':f'Bearer {op}'},json={'status':'delivered'})
    assert r.status_code==409

def test_client_cannot_change_operator_status(client):
    t=token(client,'client@test.com','client')
    req=client.post('/requests',headers={'Authorization':f'Bearer {t}'},json={'task_name':'pick cup','episodes_requested':1,'deadline':'2026-10-10T10:00:00Z'}).json()
    r=client.post(f"/requests/{req['id']}/status",headers={'Authorization':f'Bearer {t}'},json={'status':'in_progress'})
    assert r.status_code==403
