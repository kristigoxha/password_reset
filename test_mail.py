import os, smtplib
from dotenv import load_dotenv

load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

print(f"Logging in as {EMAIL_ADDRESS!r}")

msg = "Subject:SMTP Test\n\nThis is a test from Python."
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.set_debuglevel(1)                # <-- verbose logging
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg)
    print("Test email sent successfully!")
except Exception as e:
    print("Error sending test email:", e)
