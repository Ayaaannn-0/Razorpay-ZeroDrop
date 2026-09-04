"""
Recovery Link Service
Generates and validates secure, time-limited signed tokens for customer retry links.
Prevents URL tampering and ensures recovery links expire safely (default: 1 hour).
"""

from typing import Optional
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def get_serializer(secret_key: str, salt: str = "payment-whisperer-recovery") -> URLSafeTimedSerializer:
    """Creates a URL-safe timed serializer using the application secret."""
    return URLSafeTimedSerializer(secret_key=secret_key, salt=salt)


def generate_recovery_token(payment_id: str, secret_key: str, salt: str = "payment-whisperer-recovery") -> str:
    """
    Generates a cryptographically signed token embedding the payment_id.
    """
    serializer = get_serializer(secret_key, salt=salt)
    return serializer.dumps({"payment_id": payment_id})


def verify_recovery_token(
    token: str,
    secret_key: str,
    max_age_seconds: int = 3600,
    salt: str = "payment-whisperer-recovery"
) -> Optional[str]:
    """
    Verifies the signed token and ensures it has not expired.
    Returns the payment_id if valid, or None if invalid/expired.
    """
    serializer = get_serializer(secret_key, salt=salt)
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        return data.get("payment_id")
    except (SignatureExpired, BadSignature, Exception):
        return None


def build_recovery_url(base_url: str, token: str) -> str:
    """Constructs the complete customer recovery URL."""
    clean_base = base_url.rstrip("/")
    return f"{clean_base}/retry/{token}"
