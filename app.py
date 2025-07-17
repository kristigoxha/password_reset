import os
import smtplib
import jwt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

db = SQLAlchemy()
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app, origins=[FRONTEND_URL])

    if test_config:
        app.config.update(test_config)
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SECRET_KEY"] = SECRET_KEY

    db.init_app(app)

    # -------------------- Routes --------------------

    @app.route("/reset-password", methods=["POST"])
    def reset_password_request():
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "Email address not found"}), 400

        token = jwt.encode({
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }, app.config["SECRET_KEY"], algorithm="HS256")

        link = f"{FRONTEND_URL}/reset.html?token={token}"
        subject = "Password Reset Request"
        message = f"Subject: {subject}\n\nClick here to reset: {link}"

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.sendmail(EMAIL_ADDRESS, email, message)
        except Exception as err:
            return jsonify({"error": "Email send failed"}), 500

        return jsonify({"message": "Password reset email sent"}), 200

    @app.route("/reset-password/confirm", methods=["POST"])
    def reset_password_confirm():
        data = request.get_json() or {}
        token = data.get("token", "")
        new_password = data.get("password", "")

        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 400
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 400

        user = User.query.filter_by(email=payload.get("email")).first()
        if not user:
            return jsonify({"error": "User not found"}), 400

        user.set_password(new_password)
        db.session.commit()
        return jsonify({"message": "Password has been reset"}), 200

    return app
