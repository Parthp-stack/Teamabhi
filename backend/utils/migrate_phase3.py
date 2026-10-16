import sqlite3
import os

def migrate_database():
    db_path = "adaptive_learning.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist yet.")
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    def add_cols(table, cols):
        existing = [c[1] for c in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        for col_name, col_type in cols:
            if col_name not in existing:
                print(f"Adding {col_name} ({col_type}) to {table}...")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")

    add_cols('sessions', [
        ('overall_review_status', "VARCHAR(50) DEFAULT 'INSUFFICIENT_DATA'"),
        ('is_reviewed', "BOOLEAN DEFAULT 0"),
        ('review_notes', "TEXT"),
        ('reviewed_by', "INTEGER"),
        ('reviewed_at', "DATETIME")
    ])

    add_cols('session_events', [
        ('student_id', "INTEGER"),
        ('assessment_id', "INTEGER"),
        ('client_event_id', "VARCHAR(100)"),
        ('server_timestamp', "DATETIME"),
        ('client_timestamp', "DATETIME"),
        ('code_location', "JSON"),
        ('revision_id', "INTEGER"),
        ('inserted_character_count', "INTEGER DEFAULT 0"),
        ('deleted_character_count', "INTEGER DEFAULT 0"),
        ('duration', "FLOAT"),
        ('review_status', "VARCHAR(50) DEFAULT 'NORMAL_RHYTHM'"),
        ('classification', "VARCHAR(100)"),
        ('classification_reason', "TEXT")
    ])

    add_cols('integrity_signals', [
        ('review_status', "VARCHAR(50) DEFAULT 'PENDING'"),
        ('trainer_notes', "TEXT"),
        ('reviewed_by', "INTEGER"),
        ('reviewed_at', "DATETIME")
    ])

    con.commit()
    con.close()
    print("Phase 3 SQLite migration finished successfully!")

if __name__ == "__main__":
    migrate_database()
