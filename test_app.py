import pytest
from app import app, db, User
import os

@pytest.fixture
def client():
    # Override config for testing
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.app_context():
        db.create_all()
        # Seed a test user
        user = User(email="test@example.com")
        user.set_password("oldpassword")
        db.session.add(user)
        db.session.commit()

    with app.test_client() as client:
        yield client

def test_reset_password_request_valid_email(client):
    res = client.post("/reset-password", json={"email": "test@example.com"})
    assert res.status_code == 200
    assert b"Password reset email sent" in res.data

def test_reset_password_request_invalid_email(client):
    res = client.post("/reset-password", json={"email": "wrong@example.com"})
    assert res.status_code == 400
    assert b"Email address not found" in res.data
