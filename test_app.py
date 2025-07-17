import pytest
import jwt
from datetime import datetime, timedelta
from app import create_app, db, User

SECRET_KEY = "test-secret-key"

@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": SECRET_KEY
    })

    with app.app_context():
        db.create_all()
        user = User(email="test@example.com")
        user.set_password("oldpassword")
        db.session.add(user)
        db.session.commit()

    return app.test_client()

# ----------------------------
# /reset-password tests
# ----------------------------

def test_reset_password_valid_email(client):
    res = client.post("/reset-password", json={"email": "test@example.com"})
    print(res.data.decode())
    assert res.status_code == 200
    assert b"Password reset email sent" in res.data

def test_reset_password_invalid_email(client):
    res = client.post("/reset-password", json={"email": "nope@example.com"})
    assert res.status_code == 400
    assert b"Email address not found" in res.data

# ----------------------------
# /reset-password/confirm tests
# ----------------------------

def test_reset_password_confirm_valid_token(client):
    token = jwt.encode(
        {
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(minutes=5)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    res = client.post("/reset-password/confirm", json={
        "token": token,
        "password": "newpassword123"
    })
    print(res.data.decode())
    assert res.status_code == 200
    assert b"Password has been reset" in res.data

def test_reset_password_confirm_expired_token(client):
    expired_token = jwt.encode(
        {
            "email": "test@example.com",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    res = client.post("/reset-password/confirm", json={
        "token": expired_token,
        "password": "anything"
    })
    assert res.status_code == 400
    assert b"Reset token has expired" in res.data

def test_reset_password_confirm_invalid_token(client):
    res = client.post("/reset-password/confirm", json={
        "token": "not-a-real-token",
        "password": "whatever"
    })
    assert res.status_code == 400
    assert b"Invalid reset token" in res.data
