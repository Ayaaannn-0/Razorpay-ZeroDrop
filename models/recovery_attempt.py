"""
Recovery Attempt Model
Tracks customer attempts to retry a failed payment and records conversion outcomes.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from models.transaction import Base


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    payment_id = Column(String(100), nullable=False, index=True)
    
    retry_method = Column(String(50), nullable=False)  # upi, alternate_card, netbanking, same_card
    success = Column(Boolean, default=False, nullable=False)
    new_payment_id = Column(String(100), nullable=True)
    
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "payment_id": self.payment_id,
            "retry_method": self.retry_method,
            "success": self.success,
            "new_payment_id": self.new_payment_id,
            "attempted_at": self.attempted_at.isoformat() if self.attempted_at else None,
        }
