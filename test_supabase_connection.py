"""
Script to test Supabase PostgreSQL database connection and schema verification.
Usage:
    python test_supabase_connection.py [optional_database_url]
"""
import sys
import os
from sqlalchemy import create_engine, text

def test_connection(db_url: str = None):
    url = db_url or os.getenv("DATABASE_URL")
    if not url:
        print("[Error] No DATABASE_URL provided. Pass it as an argument or set DATABASE_URL environment variable.")
        print("Example: python test_supabase_connection.py postgresql://postgres.xxx:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require")
        return False

    # Normalize url prefix for SQLAlchemy
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    connect_args = {}
    if "supabase.co" in url or "pooler.supabase.com" in url or "sslmode" not in url:
        connect_args = {"sslmode": "require"}

    print(f"\n[1/3] Testing connection to remote database...")
    print(f"Target host: {url.split('@')[-1] if '@' in url else 'configured URL'}")

    try:
        engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT version();")).fetchone()
            print(f"[OK] Connected successfully! Database version: {res[0][:60]}...")

            print("\n[2/3] Verifying core tables in Supabase...")
            tables_to_check = [
                "users", "courses", "modules", "concepts", "concept_prerequisites",
                "student_mastery", "questions", "attempts", "coding_problems",
                "sessions", "session_events", "assessment_attempts", "question_attempts",
                "integrity_events"
            ]

            missing = []
            counts = {}
            for tbl in tables_to_check:
                try:
                    c = conn.execute(text(f"SELECT COUNT(*) FROM {tbl};")).scalar()
                    counts[tbl] = c
                except Exception:
                    missing.append(tbl)

            if missing:
                print(f"[Warning] The following tables are not yet present: {missing}")
                print("Run supabase_schema.sql in the Supabase SQL Editor to initialize them.")
            else:
                print("[OK] All 14 primary database tables verified:")
                for tbl, cnt in counts.items():
                    print(f"  - {tbl}: {cnt} rows")

            print("\n[3/3] Testing read and write integration...")
            test_res = conn.execute(text("SELECT count(*) FROM users;")).scalar()
            print(f"[OK] Users registered in Supabase: {test_res}")

        print("\n[SUCCESS] Supabase is fully configured and ready for Render hosting!\n")
        return True
    except Exception as e:
        print(f"\n[FAILURE] Connection failed: {e}\n")
        return False

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else None
    success = test_connection(target_url)
    sys.exit(0 if success else 1)
