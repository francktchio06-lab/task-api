import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.database import Base

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_create_task():
    response = client.post("/tasks", json={"title": "Écrire les tests"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Écrire les tests"
    assert data["done"] is False
    assert "id" in data

def test_list_tasks():
    client.post("/tasks", json={"title": "Tâche 1"})
    client.post("/tasks", json={"title": "Tâche 2"})
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_task():
    created = client.post("/tasks", json={"title": "Tâche unique"}).json()
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Tâche unique"

def test_get_task_not_found():
    response = client.get("/tasks/999")
    assert response.status_code == 404

def test_delete_task():
    created = client.post("/tasks", json={"title": "À supprimer"}).json()
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 200
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 404