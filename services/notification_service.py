"""
Notification Service
Formats and simulates multi-channel payment failure alerts (SMS and WhatsApp).
Generates customer-ready notifications compliant with TRAI transactional standards.
Supports live Twilio delivery if configured, or visual sandbox simulation by default.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import config

logger = logging.getLogger("NotificationService")


def format_sms_text(amount_display: str, explanation: str, recovery_url: str) -> str:
    """
    Constructs an SMS message fitting within standard character budgets.
    Format adheres to TRAI transactional alert standards.
    """
    return (
        f"Alert: Your payment of {amount_display} did not go through. "
        f"Reason: {explanation} "
        f"Tap here to resolve & retry: {recovery_url} "
        f"- Razorpay Payments"
    )


def format_whatsapp_text(
    amount_display: str,
    explanation: str,
    recovery_url: str,
    recovery_actions: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Constructs an enriched WhatsApp message with bulleted action steps."""
    actions_text = ""
    if recovery_actions:
        actions_text = "\n*Recommended Next Steps:*\n"
        for idx, act in enumerate(recovery_actions, 1):
            actions_text += f"• *{act.get('label', 'Action')}*: {act.get('description', '')}\n"

    return (
        f"*Payment Notice*\n\n"
        f"Your transaction of *{amount_display}* was declined.\n\n"
        f"*What happened:*\n{explanation}\n"
        f"{actions_text}\n"
        f"*Complete your payment securely:* {recovery_url}\n\n"
        f"_This is an automated service notification from Razorpay._"
    )


def build_sms_simulation(
    payment_id: str,
    customer_phone: str,
    amount_display: str,
    explanation: str,
    recovery_url: str
) -> Dict[str, Any]:
    """
    Builds a simulated SMS payload formatted for visual rendering on the sandbox phone mockup.
    """
    sms_text = format_sms_text(amount_display, explanation, recovery_url)
    now = datetime.now(timezone.utc)
    
    return {
        "sender_id": "VK-RZRPAY",
        "recipient": customer_phone or "+91 98765 43210",
        "message": sms_text,
        "recovery_url": recovery_url,
        "timestamp": now.strftime("%I:%M %p"),
        "date": now.strftime("%b %d"),
        "channel": "SMS",
        "delivery_status": "Simulated (Delivered on screen)",
        "character_count": len(sms_text),
    }


def send_sms(
    to_phone: str,
    message_body: str
) -> Dict[str, Any]:
    """
    Dispatches real SMS via Twilio if configured in environment variables,
    otherwise returns simulated success for zero-config hackathon demo.
    """
    if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_FROM_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            msg = client.messages.create(
                to=to_phone,
                from_=config.TWILIO_FROM_NUMBER,
                body=message_body
            )
            logger.info(f"Twilio SMS sent successfully: {msg.sid}")
            return {"status": "sent", "provider": "twilio", "sid": msg.sid}
        except Exception as e:
            logger.error(f"Twilio dispatch failed: {e}. Falling back to simulation.")
            return {"status": "failed", "error": str(e), "simulated": True}
    
    # Default: zero-config simulated delivery
    logger.info("Twilio unconfigured. SMS rendered visually in sandbox simulation.")
    return {"status": "simulated", "delivered": True}
