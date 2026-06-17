"""API integration tests using an isolated in-memory SQLite database."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import seed_default_users
from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_default_users(db)
    db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


client = TestClient(app)


def _token(username="admin", password=None):
    pwd = password or {"admin": "admin123", "engineer": "engineer123", "analyst": "analyst123"}[username]
    resp = client.post("/auth/login", data={"username": username, "password": pwd})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _headers(username="admin"):
    return {"Authorization": f"Bearer {_token(username)}"}


def _make_customer(email="a@b.com", username="admin"):
    return client.post("/customers", json={
        "name": "Alice", "email": email, "phone": "1234567890", "city": "Chennai"
    }, headers=_headers(username))


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_login_invalid_credentials():
    assert client.post("/auth/login", data={"username": "admin", "password": "wrong"}).status_code == 401


def test_unauthenticated_request_rejected():
    assert client.get("/customers").status_code == 401


def test_create_and_list_customer():
    resp = _make_customer()
    assert resp.status_code == 201
    assert resp.json()["customer_id"] == 1
    assert len(client.get("/customers", headers=_headers()).json()) == 1


def test_duplicate_email_rejected():
    _make_customer()
    assert _make_customer().status_code == 409


def test_invalid_email_rejected():
    resp = client.post("/customers", json={"name": "Bad", "email": "not-an-email"}, headers=_headers())
    assert resp.status_code == 422


def test_update_customer():
    _make_customer()
    resp = client.put("/customers/1", json={"city": "Mumbai"}, headers=_headers())
    assert resp.status_code == 200
    assert resp.json()["city"] == "Mumbai"


def test_analyst_cannot_write():
    """RBAC: analyst is read-only."""
    resp = client.post("/customers", json={
        "name": "X", "email": "x@y.com"
    }, headers=_headers("analyst"))
    assert resp.status_code == 403


def test_analyst_can_read():
    _make_customer()
    assert client.get("/customers", headers=_headers("analyst")).status_code == 200


def test_order_requires_existing_customer():
    resp = client.post("/orders", json={
        "customer_id": 999, "product_name": "Widget", "quantity": 2,
        "amount": 50.0, "order_date": "2024-01-01"
    }, headers=_headers())
    assert resp.status_code == 400


def test_order_amount_must_be_positive():
    _make_customer()
    resp = client.post("/orders", json={
        "customer_id": 1, "product_name": "Widget", "quantity": 1,
        "amount": -5, "order_date": "2024-01-01"
    }, headers=_headers())
    assert resp.status_code == 422


def test_dashboard_metrics():
    _make_customer()
    client.post("/orders", json={
        "customer_id": 1, "product_name": "Widget", "quantity": 2,
        "amount": 100.0, "order_date": "2024-01-01"
    }, headers=_headers())
    data = client.get("/dashboard/metrics", headers=_headers()).json()
    assert data["total_orders"] == 1
    assert float(data["total_revenue"]) == 100.0
    assert data["total_customers"] == 1
    assert data["top_customers"][0]["name"] == "Alice"


def test_audit_log_records_writes():
    _make_customer()
    logs = client.get("/auth/audit", headers=_headers()).json()
    actions = {(l["action"], l["resource"]) for l in logs}
    assert ("CREATE", "customers") in actions


def test_audit_requires_admin():
    assert client.get("/auth/audit", headers=_headers("analyst")).status_code == 403
