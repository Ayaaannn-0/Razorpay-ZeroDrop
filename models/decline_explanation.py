"""
Decline Explanation Model
Stores generated AI explanations and recommended recovery action bundles.
"""

import json
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from models.transaction import Base


class DeclineExplanation(Base):
    __tablename__ = "decline_explanations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    payment_id = Column(String(100), nullable=False, index=True)
    
    explanation = Column(Text, nullable=False)
    recovery_actions_json = Column(Text, nullable=False)  # JSON-encoded array of action dicts
    
    retry_recommended = Column(String(10), default="true")
    estimated_retry_window = Column(String(100), default="Immediate")
    
    source = Column(String(50), default="groq")  # groq or rule_engine_fallback
    model_used = Column(String(100), default="llama-3.3-70b-versatile")
    confidence_score = Column(Float, default=0.95)
    latency_ms = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def recovery_actions(self):
        try:
            return json.loads(self.recovery_actions_json)
        except Exception:
            return []

    @recovery_actions.setter
    def recovery_actions(self, actions_list):
        self.recovery_actions_json = json.dumps(actions_list)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "payment_id": self.payment_id,
            "explanation": self.explanation,
            "recovery_actions": self.recovery_actions,
            "retry_recommended": self.retry_recommended == "true",
            "estimated_retry_window": self.estimated_retry_window,
            "source": self.source,
            "model_used": self.model_used,
            "confidence_score": self.confidence_score,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
