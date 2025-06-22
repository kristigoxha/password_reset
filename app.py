from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://loveupookie.com"])

EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    user_email = data.get("email")

    if not user_email or "@" not in user_email:
        return jsonify({"error": "Invalid email"}), 400

    reset_link = f"https://your-website.com/reset-password.html?email={user_email}"
    subject = "Your Password Reset Link"
    body = f"""
    Hello,

    Click the link below to reset your password:
    {reset_link}

    If you didn't request this, you can safely ignore this email.

    Thanks,
    Your Website Team
    """

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = user_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, user_email, msg.as_string())

        return jsonify({"message": "Reset email sent!"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Failed to send email"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
