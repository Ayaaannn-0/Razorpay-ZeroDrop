"""
Transaction Model
Stores ingested failed transactions and metadata per ARCHITECTURE.md.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # in paise (e.g. 50000 = ₹500.00)
    amount_rupees = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(String(50), nullable=False)  # card, upi, netbanking
    
    # Error metadata extracted from Razorpay webhook
    error_code = Column(String(100), nullable=False)
    error_reason = Column(String(100), nullable=False, index=True)
    error_source = Column(String(50), nullable=False)
    error_step = Column(String(50), nullable=False)
    error_description = Column(Text, nullable=False)

    # Customer identifiers (masked for PII privacy)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)

    # Instrument metadata
    card_network = Column(String(50), nullable=True)
    card_issuer = Column(String(100), nullable=True)
    card_type = Column(String(50), nullable=True)
    card_last4 = Column(String(10), nullable=True)
    vpa = Column(String(100), nullable=True)

    status = Column(String(50), default="failed", nullable=False)  # failed, recovery_initiated, recovered
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "amount": self.amount,
            "amount_rupees": self.amount_rupees,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "error_code": self.error_code,
            "error_reason": self.error_reason,
            "error_source": self.error_source,
            "error_step": self.error_step,
            "error_description": self.error_description,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "card_network": self.card_network,
            "card_issuer": self.card_issuer,
            "card_last4": self.card_last4,
            "vpa": self.vpa,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
