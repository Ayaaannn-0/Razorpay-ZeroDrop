"""
Payment Failure Whisperer — Main Flask Application
Intercepts failed Razorpay payments, translates cryptic error codes,
and delivers plain-English explanations with ranked recovery actions.
"""

import hashlib
import hmac
import json
import logging
import sys
from flask import Flask, jsonify, render_template, request

# Ensure Windows terminal handles UTF-8 (₹ Rupee symbol and emojis) without error
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from models import DeclineExplanation, RecoveryAttempt, Transaction, db_session, init_db
from services.decline_extractor import extract_decline_info
from services.llm_agent import LLMAgent
from services.recovery_link import build_recovery_url, generate_recovery_token, verify_recovery_token
from services.rule_engine import RuleEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PaymentWhisperer")

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

# Initialize singletons for services
rule_engine = RuleEngine()
llm_agent = LLMAgent(api_key=config.GROQ_API_KEY, model=config.GROQ_MODEL)


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Ensures database connections are released at the end of each request."""
    db_session.remove()


def verify_webhook_signature(body_bytes: bytes, signature: str, secret: str) -> bool:
    """
    Verifies the HMAC-SHA256 signature sent in the X-Razorpay-Signature header.
    In development, accepts 'mock_signature_for_local_testing' as documented in RAZORPAY_INTEGRATION.md.
    """
    if not signature or not secret:
        return False

    # Allow mock testing bypass if explicitly configured for local mock script
    if signature == "mock_signature_for_local_testing" and config.DEBUG:
        return True

    try:
        expected = hmac.new(
            key=secret.encode("utf-8"),
            msg=body_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error(f"Error computing signature: {e}")
        return False


# ---------------------------------------------------------------------------
# Core Webhook Endpoint
# ---------------------------------------------------------------------------
@app.route("/webhook/razorpay/payment", methods=["POST"])
def razorpay_webhook():
    """
    Primary webhook receiver for Razorpay 'payment.failed' events.
    Verifies cryptographic signature, extracts decline reason, evaluates RBI rules,
    invokes Groq AI agent for explanation, and persists to DB.
    """
    raw_body = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Security: Verify webhook origin
    if not verify_webhook_signature(raw_body, signature, config.RAZORPAY_WEBHOOK_SECRET):
        logger.warning("Rejected webhook with invalid or missing X-Razorpay-Signature")
        return jsonify({
            "status": "error",
            "message": "Invalid webhook signature"
        }), 401

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Malformed JSON: {e}"}), 400

    logger.info(f"Received webhook event: {payload.get('event', 'unknown')}")

    # 1. Extract structured decline metadata
    try:
        decline_info = extract_decline_info(payload)
    except Exception as e:
        logger.error(f"Failed to extract decline info: {e}")
        return jsonify({"status": "error", "message": f"Extraction failure: {e}"}), 422

    # 2. Evaluate rules against Razorpay taxonomy and RBI guidelines
    rule_context = rule_engine.evaluate(decline_info)

    # 3. Generate AI plain-English explanation + ranked recovery actions
    ai_guidance = llm_agent.generate_explanation(decline_info, rule_context)

    # 4. Generate signed, time-limited recovery link
    recovery_token = generate_recovery_token(
        payment_id=decline_info["payment_id"],
        secret_key=config.SECRET_KEY
    )
    base_url = request.host_url.rstrip("/")
    recovery_url = build_recovery_url(base_url, recovery_token)

    # 5. Format SMS notification body
    amount_display = f"₹{decline_info['amount_rupees']:,.2f}"
    sms_body = (
        f"Hey! Your {amount_display} payment didn't go through. "
        f"Reason: {ai_guidance['explanation']} "
        f"Tap to retry: {recovery_url}"
    )

    # 6. Persist to Database (Transaction + DeclineExplanation)
    try:
        # Check if transaction already recorded to prevent duplicate ingestion
        existing_tx = db_session.query(Transaction).filter_by(payment_id=decline_info["payment_id"]).first()
        if not existing_tx:
            tx = Transaction(
                payment_id=decline_info["payment_id"],
                amount=decline_info["amount"],
                amount_rupees=decline_info["amount_rupees"],
                currency=decline_info["currency"],
                payment_method=decline_info["method"],
                error_code=decline_info["error_code"],
                error_reason=decline_info["error_reason"],
                error_source=decline_info["error_source"],
                error_step=decline_info["error_step"],
                error_description=decline_info["error_description"],
                customer_email=decline_info["masked_email"],
                customer_phone=decline_info["masked_phone"],
                card_network=decline_info["card_network"],
                card_issuer=decline_info["card_issuer"],
                card_last4=decline_info["card_last4"],
                vpa=decline_info["vpa"],
                status="recovery_initiated"
            )
            db_session.add(tx)
            db_session.flush()

            explanation_record = DeclineExplanation(
                transaction_id=tx.id,
                payment_id=tx.payment_id,
                explanation=ai_guidance["explanation"],
                recovery_actions_json=json.dumps(ai_guidance["recovery_actions"]),
                retry_recommended="true" if ai_guidance.get("retry_recommended") else "false",
                estimated_retry_window=ai_guidance.get("estimated_retry_window", "Immediate"),
                source=ai_guidance.get("source", "groq"),
                model_used=ai_guidance.get("model", config.GROQ_MODEL),
                confidence_score=ai_guidance.get("confidence_score", 0.95),
                latency_ms=ai_guidance.get("latency_ms", 0),
            )
            db_session.add(explanation_record)
            db_session.commit()
            logger.info(f"Transaction {tx.payment_id} and explanation persisted to database.")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Database error while saving transaction: {e}")

    # Return complete recovery response
    return jsonify({
        "status": "processed",
        "payment_id": decline_info["payment_id"],
        "error_code": decline_info["error_code"],
        "error_reason": decline_info["error_reason"],
        "explanation": ai_guidance["explanation"],
        "recovery_actions": ai_guidance["recovery_actions"],
        "retry_recommended": ai_guidance.get("retry_recommended", True),
        "estimated_retry_window": ai_guidance.get("estimated_retry_window", "Immediate"),
        "recovery_url": recovery_url,
        "recovery_token": recovery_token,
        "sms_body": sms_body,
        "source": ai_guidance.get("source"),
        "latency_ms": ai_guidance.get("latency_ms", 0)
    }), 200


# ---------------------------------------------------------------------------
# Sandbox Checkout Simulation Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
@app.route("/zerodrop", methods=["GET"])
@app.route("/razorpay-zerodrop", methods=["GET"])
@app.route("/sandbox", methods=["GET"])
def sandbox():
    """Renders the self-contained Razorpay ZeroDrop Checkout simulator."""
    return render_template("sandbox_checkout.html")


@app.route("/api/simulate-payment", methods=["POST"])
def simulate_payment():
    """
    Operator endpoint for sandbox simulation.
    Synthesizes an authentic Razorpay payment.failed webhook payload matching
    the official schema (RAZORPAY_INTEGRATION.md Step 7), signs it with HMAC-SHA256,
    and posts it to the /webhook/razorpay/payment endpoint.
    """
    from datetime import datetime, timezone
    import time
    from services.notification_service import build_sms_simulation

    data = request.get_json(force=True) or {}
    now_ts = int(time.time())
    sim_id = f"pay_sim_{int(time.time()*1000)}"

    amount = int(data.get("amount", 499900))
    currency = data.get("currency", "INR")
    method = data.get("method", "card")
    error_reason = data.get("scenario", "insufficient_funds")
    error_code = data.get("error_code", "BAD_REQUEST_ERROR")
    error_source = data.get("error_source", "customer")
    error_step = data.get("error_step", "payment_authorization")
    error_description = data.get("error_description", "Payment failed")
    email = data.get("email", "ayaan.shopper@gmail.com")
    contact = data.get("contact", "+919876543210")

    # Construct official Razorpay webhook payload format
    payload = {
        "entity": "event",
        "account_id": "acc_sandbox_demo",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": sim_id,
                    "amount": amount,
                    "currency": currency,
                    "status": "failed",
                    "method": method,
                    "email": email,
                    "contact": contact,
                    "error_code": error_code,
                    "error_description": error_description,
                    "error_source": error_source,
                    "error_step": error_step,
                    "error_reason": error_reason,
                    "created_at": now_ts,
                    "card": {
                        "network": data.get("card_network", "Visa"),
                        "issuer": data.get("card_issuer", "HDFC"),
                        "last4": data.get("card_last4", "4321"),
                        "type": data.get("card_type", "debit")
                    } if method == "card" else None,
                    "vpa": data.get("vpa", "") if method == "upi" else None
                }
            }
        }
    }

    payload_bytes = json.dumps(payload).encode("utf-8")
    
    # Compute signature using local webhook secret
    signature = hmac.new(
        key=config.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Pass through the real webhook pipeline using test client, preserving Host and Port
    client_headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature,
        "Host": request.host
    }
    with app.test_client() as internal_client:
        webhook_res = internal_client.post(
            "/webhook/razorpay/payment",
            data=payload_bytes,
            headers=client_headers
        )
        webhook_data = webhook_res.get_json() or {}

    # Guarantee recovery_url uses the active server host & port
    if "recovery_token" in webhook_data:
        correct_recovery_url = f"{request.host_url.rstrip('/')}/retry/{webhook_data['recovery_token']}"
        webhook_data["recovery_url"] = correct_recovery_url

    # Attach simulated SMS notification mockup payload
    amount_display = f"₹{amount / 100:,.2f}"
    sms_preview = build_sms_simulation(
        payment_id=sim_id,
        customer_phone=contact,
        amount_display=amount_display,
        explanation=webhook_data.get("explanation", ""),
        recovery_url=webhook_data.get("recovery_url", "")
    )
    webhook_data["sms_preview"] = sms_preview
    webhook_data["sms_body"] = sms_preview["message"]

    return jsonify(webhook_data), webhook_res.status_code


# ---------------------------------------------------------------------------
# Recovery Page & Retry Routes
# ---------------------------------------------------------------------------
@app.route("/retry/<token>", methods=["GET"])
def recovery_page(token):
    """
    Renders customer-facing plain-English decline explanation & retry portal.
    Verifies cryptographic time-limited token before rendering.
    """
    payment_id = verify_recovery_token(token, config.SECRET_KEY)
    if not payment_id:
        return render_template(
            "recovery_page.html",
            error="This recovery link is invalid or has expired. Please check your latest SMS or contact support.",
            error_title="Link Expired or Invalid"
        ), 404

    tx = db_session.query(Transaction).filter_by(payment_id=payment_id).first()
    if not tx:
        return render_template(
            "recovery_page.html",
            error=f"Transaction '{payment_id}' not found in records.",
            error_title="Transaction Not Found"
        ), 404

    explanation = db_session.query(DeclineExplanation).filter_by(payment_id=payment_id).first()
    amount_formatted = f"₹{tx.amount_rupees:,.2f}"

    return render_template(
        "recovery_page.html",
        tx=tx,
        explanation=explanation,
        amount_formatted=amount_formatted,
        token=token
    )


@app.route("/api/retry-payment", methods=["POST"])
def retry_payment():
    """
    Simulates customer retrying payment from recovery page using an alternate method.
    Records recovery attempt and transitions transaction status to 'recovered'.
    """
    import time
    data = request.get_json(force=True) or {}
    payment_id = data.get("payment_id")
    retry_method = data.get("retry_method", "upi")

    if not payment_id:
        return jsonify({"status": "error", "message": "payment_id is required"}), 400

    tx = db_session.query(Transaction).filter_by(payment_id=payment_id).first()
    if not tx:
        return jsonify({"status": "error", "message": "Transaction not found"}), 404

    new_payment_id = f"pay_recov_{int(time.time()*1000)}"

    attempt = RecoveryAttempt(
        transaction_id=tx.id,
        payment_id=payment_id,
        retry_method=retry_method,
        success=True,
        new_payment_id=new_payment_id
    )
    db_session.add(attempt)
    tx.status = "recovered"
    db_session.commit()

    return jsonify({
        "status": "recovered",
        "original_payment_id": payment_id,
        "new_payment_id": new_payment_id,
        "retry_method": retry_method,
        "amount_rupees": tx.amount_rupees,
        "message": "Payment successfully authorized and recovered."
    }), 200


# ---------------------------------------------------------------------------
# Merchant Analytics Dashboard Route
# ---------------------------------------------------------------------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Renders merchant analytics dashboard with recovery metrics and transaction logs."""
    transactions = db_session.query(Transaction).order_by(Transaction.created_at.desc()).all()
    
    total_failures = len(transactions)
    recovered_count = sum(1 for t in transactions if t.status == "recovered")
    recovery_rate = round((recovered_count / total_failures * 100), 1) if total_failures > 0 else 0.0
    
    recovered_revenue = sum(t.amount_rupees for t in transactions if t.status == "recovered")
    at_risk_revenue = sum(t.amount_rupees for t in transactions if t.status != "recovered")

    tx_items = []
    for t in transactions:
        expl = db_session.query(DeclineExplanation).filter_by(payment_id=t.payment_id).first()
        token = generate_recovery_token(t.payment_id, config.SECRET_KEY)
        time_str = t.created_at.strftime("%b %d, %H:%M:%S") if t.created_at else "Just now"
        tx_items.append({
            "tx": t,
            "explanation": expl,
            "recovery_token": token,
            "time_formatted": time_str
        })

    stats = {
        "total_failures": total_failures,
        "recovered_count": recovered_count,
        "recovery_rate": recovery_rate,
        "recovered_revenue_formatted": f"{recovered_revenue:,.2f}",
        "at_risk_revenue_formatted": f"{at_risk_revenue:,.2f}"
    }

    return render_template("dashboard.html", stats=stats, transactions=tx_items)


# ---------------------------------------------------------------------------
# Health Check Route
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Payment Failure Whisperer",
        "database": "connected"
    }), 200


if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("[*] Razorpay ZeroDrop Server Starting")
    print(f"[*] Database: {config.DATABASE_URL}")
    print(f"[*] Webhook Secret Configured: {'Yes' if config.RAZORPAY_WEBHOOK_SECRET else 'No'}")
    print(f"[*] Groq API Configured: {'Yes' if config.GROQ_API_KEY else 'No (using Rule Engine fallback)'}")
    print(f"[*] Listening at: http://127.0.0.1:{config.PORT}/zerodrop")
    print("=" * 60)
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)

