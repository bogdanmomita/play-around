from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Read the database URL from environment variables
# Format: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/todos")

# The engine is the core interface to the database.
# It manages the connection pool — a set of reusable connections
# so we don't open/close a new connection on every request.
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory that creates new database sessions.
# Each request gets its own session (its own "conversation" with the DB).
# autocommit=False means we control when to save changes.
# autoflush=False means SQLAlchemy won't auto-send SQL before every query.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all our database models will inherit from.
# SQLAlchemy uses it to track which classes represent database tables.
Base = declarative_base()


def get_db():
    """
    Dependency function that provides a database session to each request.
    
    This is a Python generator (uses 'yield' instead of 'return').
    FastAPI calls it before the request, injects the session,
    and guarantees the session is closed after the request finishes —
    even if an error occurs. This is the 'dependency injection' pattern.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
