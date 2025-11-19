import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from main_orm import app, connect

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def connect_override():
        return session
    app.dependency_overrides[connect] = connect_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

from main_orm import User

def test_get_user(session: Session, client: TestClient):
    # add test data on backend
    test_user = User(name="Paul Grogan")
    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    # test api route
    response = client.get(f"/users/{test_user.id}")
    data = response.json()
    assert data["name"] == test_user.name

def test_get_missing_satellite(session: Session, client: TestClient):
    response = client.get(f"/users/1")
    assert response.status_code == 404