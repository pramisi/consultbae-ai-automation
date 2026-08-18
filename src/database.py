import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "consultbae.db"


def get_connection():
    """Create and return a SQLite database connection."""
    connection = sqlite3.connect(DATABASE_PATH)

    # Allows us to access columns by name
    connection.row_factory = sqlite3.Row

    return connection


def create_tables(connection):
    """Create all database tables required for Task 1."""

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            normalized_name TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS naukri_applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            source_row INTEGER,

            full_name_raw TEXT,
            email_raw TEXT,
            phone_raw TEXT,
            city_raw TEXT,

            experience_years REAL,

            current_ctc_raw TEXT,
            current_ctc_inr INTEGER,

            applied_date_raw TEXT,
            applied_date TEXT,

            skills_raw TEXT,
            skills_json TEXT,

            FOREIGN KEY (person_id)
                REFERENCES people(person_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gig_workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            source_row INTEGER,

            email_raw TEXT,
            worker_name_raw TEXT,

            rate_raw TEXT,
            rate_value REAL,
            rate_unit TEXT,

            location_raw TEXT,
            status_raw TEXT,

            skill_tags_raw TEXT,
            skill_tags_json TEXT,

            FOREIGN KEY (person_id)
                REFERENCES people(person_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cbnexus_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            source_row INTEGER,

            name_raw TEXT,
            phone_raw TEXT,
            city_raw TEXT,

            verified_raw TEXT,
            verified INTEGER,

            projects_completed INTEGER,

            FOREIGN KEY (person_id)
                REFERENCES people(person_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_quality_issues (
            issue_id INTEGER PRIMARY KEY AUTOINCREMENT,

            source_name TEXT,
            source_row INTEGER,

            issue_type TEXT,
            description TEXT,
            action_taken TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,

            source_name TEXT,
            source_row INTEGER,

            source_name_value TEXT,
            source_email TEXT,
            source_phone TEXT,

            confidence INTEGER,
            reason TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()


def clear_database(connection):
    """
    Clear generated data before a fresh pipeline run.
    Source CSV files are never modified.
    """

    cursor = connection.cursor()

    cursor.execute("DELETE FROM naukri_applicants")
    cursor.execute("DELETE FROM gig_workers")
    cursor.execute("DELETE FROM cbnexus_contacts")
    cursor.execute("DELETE FROM data_quality_issues")
    cursor.execute("DELETE FROM match_reviews")
    cursor.execute("DELETE FROM people")

    connection.commit()