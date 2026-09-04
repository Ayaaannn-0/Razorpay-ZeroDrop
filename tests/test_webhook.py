"""
Integration Tests for Razorpay Webhook Endpoint
Tests cryptographic HMAC signature validation, error handling, and pipeline execution.
"""

import hashlib
import hmac
import json
import pytest
from app import app
import config
from models import DeclineExplanation, Transaction, db_session, init_db


@pytest.fixture(autouse=True)
def setup_database():
    """Ensures clean DB before each test."""
    init_db()
    yield
    db_session.remove()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def compute_signature(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def test_webhook_valid_signature_and_processing(client):
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_webhook_001",
                    "amount": 499900,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "email": "test@example.com",
                    "contact": "+919876543210",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "The customer does not have sufficient funds in the account to complete the payment.",
                    "error_source": "customer",
                    "error_step": "payment_authorization",
                    "error_reason": "insufficient_funds",
                    "card": {
                        "network": "Visa",
                        "issuer": "HDFC",
                        "last4": "4321",
                        "type": "debit"
                    },
                    "created_at": 1735689600
                }
            }
        }
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = compute_signature(payload_bytes, config.RAZORPAY_WEBHOOK_SECRET)

    response = client.post(
        "/webhook/razorpay/payment",
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature
        }
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "processed"
    assert data["payment_id"] == "pay_test_webhook_001"
    assert data["error_reason"] == "insufficient_funds"
    assert "explanation" in data
    assert len(data["recovery_actions"]) >= 1
    assert "recovery_url" in data

    # Verify DB persistence
    tx = db_session.query(Transaction).filter_by(payment_id="pay_test_webhook_001").first()
    assert tx is not None
    assert tx.amount == 499900

    explanation = db_session.query(DeclineExplanation).filter_by(payment_id="pay_test_webhook_001").first()
    assert explanation is not None
    assert len(explanation.recovery_actions) >= 1


def test_webhook_invalid_signature_rejected(client):
    payload = {"event": "payment.failed", "payload": {}}
    payload_bytes = json.dumps(payload).encode("utf-8")
    fake_signature = "bad_hex_signature_abcdef123456"

    response = client.post(
        "/webhook/razorpay/payment",
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": fake_signature
        }
    )

    assert response.status_code == 401
    data = response.get_json()
    assert data["status"] == "error"
    assert "Invalid webhook signature" in data["message"]


def test_webhook_missing_signature_rejected(client):
    payload = {"event": "payment.failed", "payload": {}}
    response = client.post(
        "/webhook/razorpay/payment",
        json=payload
    )
    assert response.status_code == 401


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"
