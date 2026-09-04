"""
Unit Tests for services/llm_agent.py
Tests fail-safe fallback logic, output formatting, and recovery actions.
"""

from services.llm_agent import LLMAgent
from services.rule_engine import RuleEngine


def test_llm_agent_fallback_mode():
    """Verify that if Groq API key is unconfigured, LLMAgent falls back seamlessly."""
    engine = RuleEngine()
    agent = LLMAgent(api_key="unconfigured")

    decline = {
        "error_reason": "card_expired",
        "error_code": "BAD_REQUEST_ERROR",
        "amount_rupees": 1500.0,
        "method": "card",
    }
    context = engine.evaluate(decline)
    result = agent.generate_explanation(decline, context)

    assert result["source"] == "rule_engine_fallback"
    assert "expired" in result["explanation"].lower()
    assert len(result["recovery_actions"]) >= 1
    assert result["retry_recommended"] is True
    assert result["estimated_retry_window"] == "Instant"


def test_llm_agent_response_keys():
    """Ensure generated explanation dictionary has all expected contract fields."""
    engine = RuleEngine()
    agent = LLMAgent()

    decline = {
        "error_reason": "bank_technical_error",
        "error_code": "GATEWAY_ERROR",
        "amount_rupees": 7500.0,
        "method": "card",
        "card_issuer": "HDFC",
    }
    context = engine.evaluate(decline)
    result = agent.generate_explanation(decline, context)

    required_keys = [
        "explanation",
        "recovery_actions",
        "retry_recommended",
        "estimated_retry_window",
        "confidence_score",
        "source",
        "model",
        "latency_ms",
    ]
    for key in required_keys:
        assert key in result, f"Result missing key '{key}'"
