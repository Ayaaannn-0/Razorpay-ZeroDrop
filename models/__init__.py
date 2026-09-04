"""
Database Models Package
Initializes SQLAlchemy engine and session, providing zero-config SQLite or PostgreSQL connectivity.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import config
from models.transaction import Base, Transaction
from models.decline_explanation import DeclineExplanation
from models.recovery_attempt import RecoveryAttempt

# Configure database engine
connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


def init_db():
    """Initializes database tables according to declared schema."""
    Base.metadata.create_all(bind=engine)


__all__ = [
    "engine",
    "db_session",
    "init_db",
    "Base",
    "Transaction",
    "DeclineExplanation",
    "RecoveryAttempt",
]
