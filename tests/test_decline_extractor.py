"""
Unit Tests for services/decline_extractor.py
Verifies extraction accuracy on authentic Razorpay webhook payloads and PII privacy masking.
"""

import pytest
from services.decline_extractor import (
    extract_decline_info,
    mask_contact,
    mask_email,
    normalize_error_code,
)


@pytest.fixture
def sample_card_webhook_payload():
    """Exact payload matching RAZORPAY_INTEGRATION.md Step 7."""
    return {
        "entity": "event",
        "account_id": "acc_ABC123",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_XYZ789",
                    "amount": 50000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "card_id": "card_ABC123",
                    "email": "test@example.com",
                    "contact": "+919876543210",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed due to insufficient funds in the customer's account.",
                    "error_source": "bank",
                    "error_step": "payment_authorization",
                    "error_reason": "insufficient_funds",
                    "card": {
                        "network": "Visa",
                        "last4": "1111",
                        "issuer": "HDFC",
                        "type": "debit"
                    },
                    "created_at": 1735689600
                }
            }
        }
    }


@pytest.fixture
def sample_upi_webhook_payload():
    """Sample UPI failure webhook payload."""
    return {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_UPI456",
                    "amount": 10500000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "email": "ayaan@example.com",
                    "contact": "+919811122233",
                    "vpa": "failure@razorpay",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "NPCI has a transaction limit both on the amount and the frequency per day.",
                    "error_source": "customer",
                    "error_step": "payment_authorization",
                    "error_reason": "transaction_frequency_limit_exceeded",
                    "created_at": 1735689600
                }
            }
        }
    }


def test_extract_card_decline(sample_card_webhook_payload):
    result = extract_decline_info(sample_card_webhook_payload)
    assert result["payment_id"] == "pay_XYZ789"
    assert result["amount"] == 50000
    assert result["amount_rupees"] == 500.0
    assert result["currency"] == "INR"
    assert result["method"] == "card"
    assert result["error_code"] == "BAD_REQUEST_ERROR"
    assert result["error_reason"] == "insufficient_funds"
    assert result["card_network"] == "Visa"
    assert result["card_issuer"] == "HDFC"
    assert result["card_last4"] == "1111"
    assert result["card_type"] == "debit"


def test_extract_upi_decline(sample_upi_webhook_payload):
    result = extract_decline_info(sample_upi_webhook_payload)
    assert result["payment_id"] == "pay_UPI456"
    assert result["amount"] == 10500000
    assert result["amount_rupees"] == 105000.0
    assert result["method"] == "upi"
    assert result["vpa"] == "failure@razorpay"
    assert result["error_reason"] == "transaction_frequency_limit_exceeded"


def test_pii_masking():
    email = "customer@example.com"
    masked_email = mask_email(email)
    assert masked_email.startswith("c")
    assert masked_email.endswith("@example.com")
    assert "*" in masked_email

    phone = "+919876543210"
    masked_phone = mask_contact(phone)
    assert masked_phone.startswith("+919")
    assert masked_phone.endswith("3210")
    assert "****" in masked_phone


def test_normalize_error_code():
    assert normalize_error_code("bad_request_error") == "BAD_REQUEST_ERROR"
    assert normalize_error_code("  gateway error ") == "GATEWAY_ERROR"
    assert normalize_error_code(None) == "UNKNOWN_ERROR"
