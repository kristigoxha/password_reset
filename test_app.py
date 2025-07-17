import json
import pytest
from app import app, db, User

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # In-memory test DB
    with app.app_context():
        db.create_all()
        test_user = User(email="test@example.com")
        test_user.set_password("oldpassword")
        db.session.add(test_user)
        db.session.commit()
    with app.test_client() as client:
        yield client

def test_reset_password_request_valid_email(client):
    response = client.post("/reset-password", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert b"Password reset email sent" in response.data

def test_reset_password_request_invalid_email(client):
    response = client.post("/reset-password", json={"email": "fake@example.com"})
    assert response.status_code == 400
    assert b"Email address not found" in response.data

def test_reset_password_confirm_valid_token(client):
    import jwt
    from datetime import datetime, timedelta
    token = jwt.encode(
        {"email": "test@example.com", "exp": datetime.utcnow() + timedelta(hours=1)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    response = client.post("/reset-password/confirm", json={
        "token": token,
        "password": "newpassword"
    })
    assert response.status_code == 200
    assert b"Password has been reset" in response.data

def test_reset_password_confirm_invalid_token(client):
    response = client.post("/reset-password/confirm", json={
        "token": "invalidtoken",
        "password": "something"
    })
    assert response.status_code == 400
