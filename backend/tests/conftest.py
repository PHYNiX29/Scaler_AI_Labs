import pytest
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.utils.seeder import seed_database


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    # Register test user and return Authorization Bearer header
    res = client.post(
        "/api/auth/register",
        json={"email": "tester@scaler.ai", "password": "password123", "name": "Test Creator"},
    )
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
