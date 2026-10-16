import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

def sanitize_db_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        # SQLAlchemy 1.4+ / 2.0 requires postgresql:// instead of postgres://
        url = "postgresql://" + url[len("postgres://"):]
    
    # Auto-encode passwords containing special characters (like '@')
    if "://" in url and url.count("@") > 1:
        scheme, rest = url.split("://", 1)
        last_at = rest.rfind("@")
        userinfo = rest[:last_at]
        hostpath = rest[last_at + 1:]
        if ":" in userinfo:
            user, pwd = userinfo.split(":", 1)
            sanitized_pwd = urllib.parse.quote_plus(pwd)
            url = f"{scheme}://{user}:{sanitized_pwd}@{hostpath}"
            
    return url

# Determine and sanitize database engine URL and parameters
db_url = sanitize_db_url(settings.DATABASE_URL)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "supabase.co" in db_url or "pooler.supabase.com" in db_url:
    # Ensure SSL is enabled for Supabase hosted instances
    if "sslmode" not in db_url:
        connect_args = {"sslmode": "require"}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    # If configured remote DB is not accessible, fallback to SQLite for local development
    fallback_url = "sqlite:///./adaptive_learning.db"
    print(f"[Database] Notice: Could not connect to {db_url} ({e}). Falling back to local SQLite: {fallback_url}")
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
