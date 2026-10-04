import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from app.main import app
from app.auth import hash_password
from app.models import User, Role

engine=create_engine('sqlite:///./test.db',connect_args={'check_same_thread':False})
TestingSession=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)

@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(engine)
    s=TestingSession()
    for email,role,pw in [('client@test.com',Role.client,'client'),('ops@test.com',Role.operator,'ops'),('admin@test.com',Role.admin,'admin')]:
        s.add(User(email=email,password_hash=hash_password(pw),name=email,role=role))
    s.commit()
    yield s
    s.close(); Base.metadata.drop_all(engine)

def override():
    s=TestingSession()
    try: yield s
    finally: s.close()
app.dependency_overrides[get_db]=override

@pytest.fixture
def client(): return TestClient(app)

def token(client,email,password):
    return client.post('/auth/login',json={'email':email,'password':password}).json()['access_token']
