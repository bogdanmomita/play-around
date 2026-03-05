import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite database for tests.
# This means tests never touch the real PostgreSQL database —
# each test run starts with a clean, empty DB and throws it away at the end.
# SQLite is file-based (or in-memory), so no server needed for testing.
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite with FastAPI
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """
    Override the real database dependency with the test database.
    FastAPI's dependency injection lets us swap out any dependency for tests.
    This is one of the biggest benefits of the Depends() pattern.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Tell FastAPI to use our test DB instead of the real one
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """
    autouse=True means this fixture runs before EVERY test automatically.
    We create all tables before each test and drop them after.
    This guarantees test isolation — each test starts with a completely clean DB.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """
    TestClient wraps our FastAPI app and lets us make HTTP requests
    without running a real server. It's synchronous and fast.
    """
    # Patch Redis so tests don't need a real Redis server
    with patch("app.cache.redis_client") as mock_redis:
        mock_redis.get.return_value = None  # Always cache miss
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = True
        yield TestClient(app)


# --- Tests ---

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_todo(client):
    response = client.post("/todos/", json={
        "title": "Buy groceries",
        "description": "Milk, eggs, bread"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["description"] == "Milk, eggs, bread"
    assert data["completed"] == False
    assert "id" in data
    assert "created_at" in data


def test_create_todo_missing_title(client):
    """FastAPI should reject requests with missing required fields."""
    response = client.post("/todos/", json={"description": "No title"})
    assert response.status_code == 422  # Unprocessable Entity


def test_get_todos_empty(client):
    response = client.get("/todos/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_todos(client):
    client.post("/todos/", json={"title": "First todo"})
    client.post("/todos/", json={"title": "Second todo"})

    response = client.get("/todos/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_todo_by_id(client):
    created = client.post("/todos/", json={"title": "Test todo"}).json()
    response = client.get(f"/todos/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test todo"


def test_get_todo_not_found(client):
    response = client.get("/todos/999")
    assert response.status_code == 404


def test_update_todo(client):
    created = client.post("/todos/", json={"title": "Old title"}).json()
    response = client.put(f"/todos/{created['id']}", json={
        "title": "New title",
        "completed": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New title"
    assert data["completed"] == True


def test_partial_update_todo(client):
    """Only updating completed should not change the title."""
    created = client.post("/todos/", json={"title": "My todo"}).json()
    response = client.put(f"/todos/{created['id']}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My todo"  # Unchanged
    assert data["completed"] == True   # Updated


def test_delete_todo(client):
    created = client.post("/todos/", json={"title": "Delete me"}).json()
    response = client.delete(f"/todos/{created['id']}")
    assert response.status_code == 204

    # Verify it's actually gone
    response = client.get(f"/todos/{created['id']}")
    assert response.status_code == 404


def test_delete_todo_not_found(client):
    response = client.delete("/todos/999")
    assert response.status_code == 404
