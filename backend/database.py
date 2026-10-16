from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# Determine database engine parameters based on database dialect
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    # If configured Postgres is not running or accessible, fallback to SQLite for local development
    fallback_url = "sqlite:///./adaptive_learning.db"
    print(f"[Database] Notice: Could not connect to {settings.DATABASE_URL} ({e}). Falling back to local SQLite: {fallback_url}")
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
