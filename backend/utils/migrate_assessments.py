import logging
from sqlalchemy import inspect, text
from backend.database import engine, Base
from backend.models.assessment_attempt import AssessmentAttempt, AssessmentWarning
from backend.models.question import Attempt
from backend.models.coding import CodingProblem

logger = logging.getLogger("migration")

def run_assessment_migrations():
    """
    Production-safe idempotent database migration.
    Preserves all existing data, adds new columns, creates tables and indexes.
    Compatible with SQLite, PostgreSQL, and Supabase.
    """
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # 1. Create AssessmentAttempt and AssessmentWarning tables if not present
        Base.metadata.create_all(
            bind=engine,
            tables=[
                AssessmentAttempt.__table__,
                AssessmentWarning.__table__
            ]
        )
        logger.info("[Migration] AssessmentAttempt & AssessmentWarning tables verified/created.")

        with engine.begin() as conn:
            # 2. Add new columns to 'attempts' table if missing
            if "attempts" in existing_tables:
                columns = [c["name"] for c in inspector.get_columns("attempts")]
                new_cols = [
                    ("assessment_id", "INTEGER"),
                    ("attempt_number", "INTEGER DEFAULT 1"),
                    ("difficulty", "VARCHAR(20)"),
                    ("concept_id", "INTEGER"),
                    ("assessment_attempt_id", "INTEGER")
                ]
                for col_name, col_type in new_cols:
                    if col_name not in columns:
                        try:
                            conn.execute(text(f"ALTER TABLE attempts ADD COLUMN {col_name} {col_type}"))
                            logger.info(f"[Migration] Added column '{col_name}' to 'attempts'.")
                        except Exception as e:
                            logger.warning(f"[Migration] Could not add '{col_name}' to 'attempts': {e}")

            # 3. Add new columns to 'coding_problems' table if missing
            if "coding_problems" in existing_tables:
                cp_columns = [c["name"] for c in inspector.get_columns("coding_problems")]
                cp_new_cols = [
                    ("problem_statement", "TEXT"),
                    ("input_format", "TEXT"),
                    ("output_format", "TEXT"),
                    ("constraints", "TEXT"),
                    ("examples", "JSON"),
                    ("expected_solution_concept", "VARCHAR(100)"),
                    ("topic", "VARCHAR(100)")
                ]
                for col_name, col_type in cp_new_cols:
                    if col_name not in cp_columns:
                        try:
                            conn.execute(text(f"ALTER TABLE coding_problems ADD COLUMN {col_name} {col_type}"))
                            logger.info(f"[Migration] Added column '{col_name}' to 'coding_problems'.")
                        except Exception as e:
                            logger.warning(f"[Migration] Could not add '{col_name}' to 'coding_problems': {e}")

            # 4. Create compatibility VIEW for coding_activity_events only if not a table
            if "coding_activity_events" not in existing_tables:
                try:
                    conn.execute(text("CREATE VIEW IF NOT EXISTS coding_activity_events AS SELECT * FROM session_events"))
                except Exception:
                    pass

            # 5. Add helpful indexes if not already present
            indexes_to_create = [
                ("idx_attempts_student_assessment", "attempts", "(student_id, assessment_id)"),
                ("idx_attempts_created_at", "attempts", "(created_at)"),
                ("idx_session_events_student_assess", "session_events", "(student_id, assessment_id)"),
                ("idx_session_events_timestamp", "session_events", "(timestamp)"),
                ("idx_asst_attempts_student", "assessment_attempts", "(student_id, assessment_id)"),
                ("idx_asst_warnings_student", "assessment_warnings", "(student_id, timestamp)")
            ]
            for idx_name, tbl_name, cols in indexes_to_create:
                if tbl_name in existing_tables or tbl_name in ["assessment_attempts", "assessment_warnings"]:
                    try:
                        conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl_name} {cols}"))
                    except Exception as e:
                        pass # Index may already exist or syntax varies slightly

        print("[Migration] Database schema migration for assessments completed successfully.")
    except Exception as e:
        logger.error(f"[Migration] Error during migration: {e}")
        print(f"[Migration] Warning during migration: {e}")

if __name__ == "__main__":
    run_assessment_migrations()
