"""
Application Configuration
Loads settings from environment variables (.env) with zero-config fallbacks for local development.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask App Secret (used for session & signed recovery links)
SECRET_KEY = os.getenv("SECRET_KEY", "whisperer-dev-secret-key-change-in-prod-9921")

# Database: Defaults to local zero-config SQLite file; switches to PostgreSQL if DATABASE_URL is set
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'payment_whisperer.db')}"
)
# SQLAlchemy requires postgresql:// instead of postgres:// if hosted on Heroku/Render
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Razorpay Credentials (from Razorpay Merchant Dashboard)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder_key")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_key_secret")

# Razorpay Webhook Secret: Used on /webhook/razorpay/payment to verify X-Razorpay-Signature
# In production, this must match the webhook secret entered in the Razorpay dashboard.
RAZORPAY_WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET",
    "whsec_local_sandbox_dev_secret_token"
)

# Groq API for ultra-fast Llama-3 inference
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "groq/compound-mini")

# Twilio Credentials (Optional for hackathon demo; SMS is visually rendered by default)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

# Server settings
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("FLASK_ENV", "development") == "development"
