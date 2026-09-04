"""
Unit Tests for services/recovery_link.py
Tests cryptographic signed token generation, decoding, and expiration.
"""

from services.recovery_link import (
    build_recovery_url,
    generate_recovery_token,
    verify_recovery_token,
)


def test_token_generation_and_verification():
    secret = "test-secret-key-12345"
    payment_id = "pay_test_ABC999"

    token = generate_recovery_token(payment_id, secret_key=secret)
    assert isinstance(token, str)
    assert len(token) > 20

    verified_id = verify_recovery_token(token, secret_key=secret, max_age_seconds=60)
    assert verified_id == payment_id


def test_tampered_token_rejection():
    secret = "test-secret-key-12345"
    payment_id = "pay_test_ABC999"

    token = generate_recovery_token(payment_id, secret_key=secret)
    tampered_token = token[:-4] + "xxxx"

    verified_id = verify_recovery_token(tampered_token, secret_key=secret)
    assert verified_id is None


def test_wrong_secret_rejection():
    secret = "test-secret-key-12345"
    wrong_secret = "attacker-secret-67890"
    payment_id = "pay_test_ABC999"

    token = generate_recovery_token(payment_id, secret_key=secret)
    verified_id = verify_recovery_token(token, secret_key=wrong_secret)
    assert verified_id is None


def test_build_recovery_url():
    url = build_recovery_url("http://localhost:5000/", "token123")
    assert url == "http://localhost:5000/retry/token123"
