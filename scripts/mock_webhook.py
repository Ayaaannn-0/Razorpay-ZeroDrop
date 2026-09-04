"""
Mock Webhook Script
Simulates Razorpay server POSTing a payment.failed event directly to your local Flask endpoint.
Useful for offline testing and live judge demos without requiring ngrok or live Razorpay keys.
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import requests

# Ensure Windows terminal handles UTF-8 (₹ Rupee symbol and emojis) without error
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Default endpoint URL
WEBHOOK_URL = "http://127.0.0.1:5000/webhook/razorpay/payment"
DEFAULT_SECRET = "whsec_local_sandbox_dev_secret_token"


def main():
    parser = argparse.ArgumentParser(description="Send mock Razorpay payment.failed webhook")
    parser.add_argument(
        "--file",
        "-f",
        default="demo/sample_payloads/insufficient_funds.json",
        help="Path to JSON payload file (default: demo/sample_payloads/insufficient_funds.json)"
    )
    parser.add_argument(
        "--url",
        "-u",
        default=WEBHOOK_URL,
        help=f"Target webhook URL (default: {WEBHOOK_URL})"
    )
    parser.add_argument(
        "--secret",
        "-s",
        default=os.getenv("RAZORPAY_WEBHOOK_SECRET", DEFAULT_SECRET),
        help="Webhook secret used for HMAC-SHA256 signing"
    )
    parser.add_argument(
        "--mock-header",
        action="store_true",
        help="Use development mock signature header ('mock_signature_for_local_testing')"
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[!] Error: Payload file not found: {args.file}")
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    payload_bytes = json.dumps(payload).encode("utf-8")

    # Generate signature
    if args.mock_header:
        signature = "mock_signature_for_local_testing"
        print("[*] Using development mock signature header")
    else:
        signature = hmac.new(args.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        print(f"[*] Generated HMAC-SHA256 signature using secret: {args.secret[:6]}...")

    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature
    }

    print(f"[*] POSTing payload to {args.url} ...")
    payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "unknown")
    print(f"[*] Payment ID: {payment_id}")

    try:
        response = requests.post(args.url, data=payload_bytes, headers=headers, timeout=10)
        print(f"\n[+] HTTP Status Code: {response.status_code}")
        try:
            res_json = response.json()
            print("[+] Parsed Recovery Response:")
            print(json.dumps(res_json, indent=2))
        except Exception:
            print("[+] Raw Response Body:")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("\n[!] Connection Error: Is the Flask server running? Run 'python app.py' first.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Request failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
