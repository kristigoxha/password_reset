import os
import smtplib
import jwt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------------
# App configuration
# ------------------------------------------------------------------
app = Flask(__name__)
CORS(app, origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")])

# Environment config
SECRET_KEY     = os.getenv("SECRET_KEY", "change_this_in_production")
EMAIL_ADDRESS  = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
SMTP_SERVER    = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 465))
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Database config (MySQL)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/reset-password", methods=["POST"])
def reset_password_request():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    print(f"[+] Reset requested for: {email}")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Email address not found"}), 400

    # Generate reset token (expires in 1 hour)
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    link = f"{FRONTEND_URL}/reset.html?token={token}"

    # Email content
    subject = "Password Reset Request"
    body = f"""
You (or someone else) requested a password reset.

Please click the link below to set a new password. This link will expire in one hour:

{link}

If you did not request this, simply ignore this email.
"""
    message = f"Subject: {subject}\n\n{body}"

    # Send email
    try:
        print("[*] Connecting to SMTP server...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.set_debuglevel(1)
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print(f"[*] Sending reset email to {email}")
            smtp.sendmail(EMAIL_ADDRESS, email, message)
        print("[+] Reset email sent successfully")
    except Exception as err:
        print("[-] SMTP error:", err)
        return jsonify({"error": "Failed to send reset email"}), 500

    return jsonify({"message": "Password reset email sent"}), 200


@app.route("/reset-password/confirm", methods=["POST"])
def reset_password_confirm():
    data = request.get_json() or {}
    token = data.get("token", "")
    new_password = data.get("password", "")

    if not token or not new_password:
        return jsonify({"error": "Token and new password are required"}), 400

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Reset token has expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid reset token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 400

    user.set_password(new_password)
    db.session.commit()
    print(f"[+] Password reset completed for: {email}")

    return jsonify({"message": "Password has been reset"}), 200

# ------------------------------------------------------------------
# Main entrypoint
# ------------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Optional seed user
        if not User.query.filter_by(email="user@example.com").first():
            u = User(email="user@example.com")
            u.set_password("old_password")
            db.session.add(u)
            db.session.commit()
            print("[*] Seeded test user: user@example.com / old_password")

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
