"""
Integration Tests for Sandbox Simulation Layer
Tests the /sandbox UI route and the /api/simulate-payment dispatch logic.
"""

from app import app
from models import Transaction, db_session, init_db


def test_sandbox_page_renders():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Payment Failure Whisperer" in html
        assert "Simulated Checkout" in html
        assert "insufficient_funds" in html
        assert "VK-RZRPAY" in html


def test_api_simulate_payment_insufficient_funds():
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        response = client.post(
            "/api/simulate-payment",
            json={
                "scenario": "insufficient_funds",
                "error_code": "BAD_REQUEST_ERROR",
                "error_source": "customer",
                "error_step": "payment_authorization",
                "error_description": "The customer does not have sufficient funds in the account to complete the payment.",
                "amount": 499900,
                "currency": "INR",
                "method": "card",
                "card_issuer": "HDFC"
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "processed"
        assert data["error_reason"] == "insufficient_funds"
        assert "explanation" in data
        assert "sms_preview" in data
        assert data["sms_preview"]["sender_id"] == "VK-RZRPAY"
        assert "recovery_url" in data


def test_api_simulate_payment_rbi_mandate():
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        response = client.post(
            "/api/simulate-payment",
            json={
                "scenario": "funds_blocked_by_mandate",
                "error_code": "BAD_REQUEST_ERROR",
                "error_source": "customer",
                "error_step": "payment_authorization",
                "error_description": "Funds are blocked by an existing mandate.",
                "amount": 1850000,  # ₹18,500
                "currency": "INR",
                "method": "card"
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "processed"
        assert "explanation" in data


def test_dashboard_renders():
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        response = client.get("/dashboard")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Merchant Dashboard" in html
        assert "Intercepted Failures" in html
        assert "Recovered Transactions" in html


def test_recovery_flow_and_retry():
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        # Simulate payment failure first
        sim_res = client.post(
            "/api/simulate-payment",
            json={
                "scenario": "card_expired",
                "error_code": "BAD_REQUEST_ERROR",
                "error_source": "customer",
                "error_step": "payment_authorization",
                "error_description": "The card has expired.",
                "amount": 499900,
                "currency": "INR",
                "method": "card"
            }
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.get_json()
        recovery_token = sim_data["recovery_token"]
        payment_id = sim_data["payment_id"]

        # View recovery page
        recov_res = client.get(f"/retry/{recovery_token}")
        assert recov_res.status_code == 200
        recov_html = recov_res.get_data(as_text=True)
        assert "Let's get your payment sorted" in recov_html
        assert payment_id in recov_html

        # Execute retry
        retry_res = client.post(
            "/api/retry-payment",
            json={
                "payment_id": payment_id,
                "retry_method": "upi"
            }
        )
        assert retry_res.status_code == 200
        retry_data = retry_res.get_json()
        assert retry_data["status"] == "recovered"
        assert "new_payment_id" in retry_data

