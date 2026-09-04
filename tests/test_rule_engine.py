"""
Unit Tests for decline_rules.json and RuleEngine
Verifies that all error codes match Razorpay's official schema and taxonomy.
"""

import json
import os
import pytest
from services.rule_engine import RuleEngine


@pytest.fixture
def rules_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", "decline_rules.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_decline_rules_json_structure(rules_data):
    """Verify top-level structure of decline_rules.json."""
    assert "version" in rules_data
    assert "source_documentation" in rules_data
    assert "rules" in rules_data
    rules = rules_data["rules"]
    assert len(rules) >= 15, "Expected at least 15 real Razorpay rules"


def test_required_fields_in_each_rule(rules_data):
    """Ensure every rule conforms to Razorpay API schema & Whisperer fields."""
    required_fields = [
        "error_reason",
        "error_code",
        "error_source",
        "error_step",
        "error_description",
        "official_next_steps",
        "category",
        "is_retryable",
        "retry_urgency",
        "suggested_methods",
        "default_plain_english_explanation",
        "default_recovery_actions",
    ]
    for reason, rule in rules_data["rules"].items():
        assert rule["error_reason"] == reason
        for field in required_fields:
            assert field in rule, f"Rule '{reason}' missing required field '{field}'"
        assert len(rule["default_recovery_actions"]) >= 1, f"Rule '{reason}' must have recovery actions"


def test_official_error_codes_sanity(rules_data):
    """Spot check core Razorpay error reasons."""
    rules = rules_data["rules"]
    assert "insufficient_funds" in rules
    assert "authentication_failed" in rules
    assert "card_expired" in rules
    assert "incorrect_cvv" in rules
    assert "bank_technical_error" in rules
    assert "funds_blocked_by_mandate" in rules
    assert "transaction_daily_limit_exceeded" in rules


def test_rule_engine_evaluation_insufficient_funds():
    """Verify rule engine evaluation on insufficient funds."""
    engine = RuleEngine()
    decline_info = {
        "error_reason": "insufficient_funds",
        "error_code": "BAD_REQUEST_ERROR",
        "amount_rupees": 2500.0,
        "method": "card",
        "card_issuer": "HDFC",
    }
    result = engine.evaluate(decline_info)
    assert result["is_retryable"] is True
    assert result["retry_urgency"] == "immediate"
    assert "HDFC" in result["bank_guidance"]
    assert len(result["fallback_actions"]) >= 2


def test_rule_engine_rbi_mandate_rule():
    """Verify RBI Recurring Mandate threshold context is applied above ₹15,000."""
    engine = RuleEngine()
    decline_info = {
        "error_reason": "funds_blocked_by_mandate",
        "error_code": "BAD_REQUEST_ERROR",
        "amount_rupees": 18500.0,  # Above ₹15,000 threshold
        "method": "card",
    }
    result = engine.evaluate(decline_info)
    assert "RBI_RECURRING_MANDATE_AFA_LIMIT" in result["applicable_rules"]
    assert "15,000" in result["rbi_context"]
