"""
Decline Code Extractor Service
Parses Razorpay payment.failed webhook payloads into standardized decline objects.
Complies with data privacy guidelines: handles masked card and contact details.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def normalize_error_code(raw_code: Optional[str]) -> str:
    """
    Standardize error code format (strip whitespace, uppercase, handle None).
    """
    if not raw_code:
        return "UNKNOWN_ERROR"
    return str(raw_code).strip().upper().replace(" ", "_")


def mask_contact(contact: Optional[str]) -> str:
    """
    Mask phone number for privacy display (e.g., +91 98765 43210 -> +91 98****3210).
    """
    if not contact:
        return ""
    contact = str(contact).strip()
    if len(contact) >= 10:
        return f"{contact[:4]}****{contact[-4:]}"
    return contact


def mask_email(email: Optional[str]) -> str:
    """
    Mask email address for privacy display (e.g., customer@example.com -> c***r@example.com).
    """
    if not email or "@" not in email:
        return ""
    parts = email.split("@")
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = f"{name[0]}{'*' * (len(name) - 2)}{name[-1]}"
    return f"{masked_name}@{domain}"


def extract_decline_info(webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a Razorpay webhook payload (specifically payment.failed event)
    and extracts a clean, normalized decline dictionary.

    Supports both standard nested Razorpay webhook format:
    {
      "entity": "event",
      "event": "payment.failed",
      "payload": {
        "payment": {
          "entity": { ... }
        }
      }
    }
    and simplified direct payment object format for versatility.
    """
    if not isinstance(webhook_payload, dict):
        raise ValueError("Webhook payload must be a dictionary")

    # Handle standard Razorpay webhook wrapper
    payment_entity: Dict[str, Any] = {}
    if "payload" in webhook_payload and "payment" in webhook_payload["payload"]:
        payment_wrapper = webhook_payload["payload"]["payment"]
        payment_entity = payment_wrapper.get("entity", payment_wrapper)
    elif "payment" in webhook_payload:
        payment_wrapper = webhook_payload["payment"]
        payment_entity = payment_wrapper.get("entity", payment_wrapper)
    else:
        payment_entity = webhook_payload

    # Extract primary transaction fields
    payment_id = payment_entity.get("id") or "pay_simulated_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    amount_in_paise = int(payment_entity.get("amount") or 0)
    amount_in_rupees = round(amount_in_paise / 100.0, 2)
    currency = payment_entity.get("currency", "INR")
    payment_method = (payment_entity.get("method") or "card").lower()
    
    # Extract error metadata
    raw_error_code = payment_entity.get("error_code") or "BAD_REQUEST_ERROR"
    error_code = normalize_error_code(raw_error_code)
    error_description = payment_entity.get("error_description") or "Payment processing failed"
    error_source = (payment_entity.get("error_source") or "bank").lower()
    error_step = (payment_entity.get("error_step") or "payment_authorization").lower()
    error_reason = (payment_entity.get("error_reason") or "generic_decline").lower()

    # Customer identifiers
    email = payment_entity.get("email", "")
    contact = payment_entity.get("contact", "")

    # Payment instrument metadata
    card_info = payment_entity.get("card") or {}
    card_network = card_info.get("network") or payment_entity.get("card_network", "")
    card_issuer = card_info.get("issuer") or payment_entity.get("card_issuer", "")
    card_type = card_info.get("type") or payment_entity.get("card_type", "")
    card_last4 = card_info.get("last4") or payment_entity.get("card_last4", "")
    vpa = payment_entity.get("vpa") or payment_entity.get("upi", {}).get("vpa", "")

    created_at_raw = payment_entity.get("created_at")
    if isinstance(created_at_raw, (int, float)):
        created_at_iso = datetime.fromtimestamp(created_at_raw, timezone.utc).isoformat()
    else:
        created_at_iso = datetime.now(timezone.utc).isoformat()

    return {
        "payment_id": payment_id,
        "amount": amount_in_paise,
        "amount_rupees": amount_in_rupees,
        "currency": currency,
        "method": payment_method,
        "error_code": error_code,
        "error_description": error_description,
        "error_source": error_source,
        "error_step": error_step,
        "error_reason": error_reason,
        "customer_email": email,
        "customer_phone": contact,
        "masked_email": mask_email(email),
        "masked_phone": mask_contact(contact),
        "card_network": card_network,
        "card_issuer": card_issuer,
        "card_type": card_type,
        "card_last4": card_last4,
        "vpa": vpa,
        "created_at": created_at_iso,
    }
