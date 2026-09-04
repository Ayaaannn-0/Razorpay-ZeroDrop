"""
Rule Engine Service
Evaluates failed transaction metadata against Razorpay error rules,
RBI compliance guidelines (e-mandate ₹15,000 threshold, UPI limits),
and bank-specific support logic.
"""

import json
import os
from typing import Any, Dict, List, Optional

# Major Indian Bank Helplines for customer recovery
BANK_HELPLINES = {
    "HDFC": {"phone": "1800-202-6161", "name": "HDFC Bank"},
    "ICICI": {"phone": "1800-1080", "name": "ICICI Bank"},
    "SBI": {"phone": "1800-1234", "name": "State Bank of India"},
    "AXIS": {"phone": "1860-419-5555", "name": "Axis Bank"},
    "KOTAK": {"phone": "1860-266-2666", "name": "Kotak Mahindra Bank"},
}

# RBI and NPCI Regulatory thresholds
RBI_MANDATE_AFA_THRESHOLD_INR = 15000.0  # ₹15,000 limit for recurring auto-debit without AFA
UPI_STANDARD_LIMIT_INR = 100000.0        # ₹1,00,000 standard daily P2M UPI cap


class RuleEngine:
    def __init__(self, rules_file_path: Optional[str] = None):
        if not rules_file_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rules_file_path = os.path.join(base_dir, "data", "decline_rules.json")
        self.rules_file_path = rules_file_path
        self.rules: Dict[str, Any] = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Loads decline rules from the JSON knowledge base."""
        if os.path.exists(self.rules_file_path):
            try:
                with open(self.rules_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("rules", {})
            except Exception as e:
                print(f"[RuleEngine] Warning: Failed to load rules file: {e}")
                return {}
        return {}

    def get_bank_info(self, issuer: Optional[str]) -> Optional[Dict[str, str]]:
        """Find helpline info for known issuing banks."""
        if not issuer:
            return None
        issuer_upper = issuer.upper().strip()
        for bank_key, bank_data in BANK_HELPLINES.items():
            if bank_key in issuer_upper:
                return bank_data
        return None

    def evaluate(self, decline_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the decline info against taxonomy rules and regulatory guidelines.
        Returns enriched contextual intelligence to guide the LLM or serve as instant fallback.
        """
        error_reason = decline_info.get("error_reason", "").lower()
        error_code = decline_info.get("error_code", "").upper()
        amount_rupees = decline_info.get("amount_rupees", 0.0)
        method = decline_info.get("method", "").lower()
        card_issuer = decline_info.get("card_issuer", "")

        # 1. Look up matching base rule in taxonomy
        rule = self.rules.get(error_reason)
        if not rule:
            # Fallback search by error_code or generic rule
            rule = {
                "error_reason": error_reason or "generic_decline",
                "error_code": error_code,
                "error_source": decline_info.get("error_source", "bank"),
                "error_step": decline_info.get("error_step", "payment_authorization"),
                "error_description": decline_info.get("error_description", "Payment could not be processed."),
                "official_next_steps": "The customer must retry with a different payment method.",
                "category": "General Payment Error",
                "is_retryable": True,
                "retry_urgency": "immediate",
                "suggested_methods": ["upi", "card", "netbanking"],
                "rbi_rule_context": None,
                "bank_guidance": None,
                "default_plain_english_explanation": "Your payment of ₹{amount} was declined by the payment gateway. Please retry or choose another payment method.",
                "default_recovery_actions": [
                    {
                        "action": "switch_to_upi",
                        "label": "Try UPI (GPay/PhonePe)",
                        "description": "UPI is currently experiencing high success rates."
                    },
                    {
                        "action": "try_different_card",
                        "label": "Use another card",
                        "description": "Try another debit or credit card."
                    }
                ]
            }

        applicable_rules: List[str] = []
        regulatory_notes: List[str] = []

        # 2. Check RBI Recurring Mandate threshold rule
        if (amount_rupees > RBI_MANDATE_AFA_THRESHOLD_INR and 
            ("mandate" in error_reason or "recurring" in error_reason or error_reason == "funds_blocked_by_mandate")):
            applicable_rules.append("RBI_RECURRING_MANDATE_AFA_LIMIT")
            regulatory_notes.append(
                f"RBI mandates Additional Factor of Authentication (AFA/OTP) for recurring charges exceeding ₹{int(RBI_MANDATE_AFA_THRESHOLD_INR):,}."
            )

        # 3. Check UPI limit rules
        if method == "upi" and amount_rupees >= UPI_STANDARD_LIMIT_INR:
            applicable_rules.append("UPI_DAILY_VALUE_LIMIT")
            regulatory_notes.append(
                f"UPI transactions are generally capped at ₹{int(UPI_STANDARD_LIMIT_INR):,} per day per bank account by NPCI."
            )

        if error_reason == "transaction_frequency_limit_exceeded":
            applicable_rules.append("NPCI_UPI_FREQUENCY_CAP")
            regulatory_notes.append(
                "NPCI guidelines and issuing banks enforce daily limits on transaction frequency per bank account."
            )

        # 4. Check International transactions rule
        if error_reason == "international_transaction_not_allowed":
            applicable_rules.append("RBI_INTERNATIONAL_OPT_IN_MANDATE")
            regulatory_notes.append(
                "Per RBI regulations, international card usage is disabled by default and must be explicitly enabled by the cardholder in netbanking/app."
            )

        # 5. Inject bank helpline if relevant
        bank_info = self.get_bank_info(card_issuer)
        bank_contact_str = ""
        if bank_info:
            bank_contact_str = f"Contact {bank_info['name']} customer care at {bank_info['phone']}."

        # Format fallback explanation with amount
        raw_fallback_template = rule.get("default_plain_english_explanation", "")
        formatted_fallback = raw_fallback_template.replace("{amount}", f"{amount_rupees:,.2f}")

        # Combine RBI context if present
        combined_rbi_context = " ".join(filter(None, [rule.get("rbi_rule_context")] + regulatory_notes))

        return {
            "matched_rule": rule,
            "applicable_rules": applicable_rules,
            "rbi_context": combined_rbi_context if combined_rbi_context else None,
            "bank_info": bank_info,
            "bank_guidance": f"{rule.get('bank_guidance', '')} {bank_contact_str}".strip(),
            "is_retryable": rule.get("is_retryable", True),
            "retry_urgency": rule.get("retry_urgency", "immediate"),
            "suggested_methods": rule.get("suggested_methods", ["upi", "card"]),
            "fallback_explanation": formatted_fallback,
            "fallback_actions": rule.get("default_recovery_actions", []),
        }
