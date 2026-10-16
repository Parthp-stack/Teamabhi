import sys
from pathlib import Path
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import sqlite3
import os
from backend.database import engine, Base
import backend.models


def migrate_database():
    # 1. Run create_all to create any non-existent tables (e.g. students, teachers, ai_evaluations)
    Base.metadata.create_all(bind=engine)

    # 2. If SQLite, add missing columns to existing tables
    db_path = "adaptive_learning.db"
    if not os.path.exists(db_path):
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    def add_cols(table, cols):
        try:
            existing = [c[1] for c in cur.execute(f"PRAGMA table_info({table})").fetchall()]
            for col_name, col_type in cols:
                if col_name not in existing:
                    print(f"Adding {col_name} ({col_type}) to {table}...")
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        except Exception as e:
            print(f"Notice on table {table}: {e}")

    add_cols('concepts', [
        ('parent_concept_id', 'INTEGER'),
        ('explanation', 'TEXT'),
        ('examples', 'JSON'),
        ('code_snippet', 'TEXT')
    ])

    add_cols('questions', [
        ('topic_id', 'INTEGER'),
        ('language', "VARCHAR(50) DEFAULT 'all'"),
        ('code_snippet', 'TEXT')
    ])

    add_cols('coding_submissions', [
        ('viva_verdict', 'VARCHAR(100)'),
        ('ai_feedback', 'TEXT')
    ])

    con.commit()
    con.close()
    print("[Database Migration] Adaptive learning schema migration verified.")

if __name__ == "__main__":
    migrate_database()
