from pathlib import Path
import json
import sqlite3


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .audio import router as audio_router


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_FILE = BASE_DIR / "consultbae.db"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="ConsultBae Automation API",
    description="API bridge between n8n and the ConsultBae SQLite database.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(audio_router)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create a connection to the ConsultBae SQLite database.
    """

    connection = sqlite3.connect(
        DATABASE_FILE,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# ENSURE SKILL CATEGORY COLUMN EXISTS
# ============================================================

def ensure_category_column():
    """
    Add skill_category to the people table if it does not
    already exist.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            PRAGMA table_info(people)
            """
        )

        columns = cursor.fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "skill_category" not in column_names:

            cursor.execute(
                """
                ALTER TABLE people
                ADD COLUMN skill_category TEXT
                """
            )

            connection.commit()

    finally:
        connection.close()


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():

    ensure_category_column()


# ============================================================
# HELPER — FIND COLUMN
# ============================================================

def get_table_columns(cursor, table_name):
    """
    Return all column names for a SQLite table.
    """

    cursor.execute(
        f"""
        PRAGMA table_info({table_name})
        """
    )

    columns = cursor.fetchall()

    return [
        column["name"]
        for column in columns
    ]


# ============================================================
# HELPER — EXTRACT SKILLS
# ============================================================

def extract_skills_from_record(record):
    """
    Look through a source record and extract fields that
    appear to contain skills.

    This avoids assuming that every source table uses
    exactly the same skill column name.
    """

    skills = []

    for column_name in record.keys():

        column_lower = column_name.lower()

        if "skill" not in column_lower:
            continue

        value = record[column_name]

        if value is None:
            continue

        if isinstance(value, str):

            value = value.strip()

            if not value:
                continue

            # Try JSON first
            try:

                parsed = json.loads(value)

                if isinstance(parsed, list):

                    for item in parsed:

                        if isinstance(item, str):
                            skills.append(item.strip())

                    continue

            except (json.JSONDecodeError, TypeError):
                pass

            # Otherwise treat as comma-separated text
            parts = value.split(",")

            for part in parts:

                cleaned = part.strip()

                if cleaned:
                    skills.append(cleaned)

        elif isinstance(value, list):

            for item in value:

                if isinstance(item, str):
                    skills.append(item.strip())

    return skills


# ============================================================
# GET PEOPLE
# ============================================================

@app.get("/api/people")
def get_people():
    """
    Return master people together with skills found in the
    Naukri and Gig Worker source records.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Get master people
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                person_id,
                full_name,
                email,
                phone,
                city,
                skill_category
            FROM people
            ORDER BY person_id
            """
        )

        people = cursor.fetchall()

        results = []

        # ----------------------------------------------------
        # Process each person
        # ----------------------------------------------------

        for person in people:

            person_id = person["person_id"]

            skills = []

            # =================================================
            # NAUKRI RECORDS
            # =================================================

            try:

                cursor.execute(
                    """
                    SELECT *
                    FROM naukri_applicants
                    WHERE person_id = ?
                    """,
                    (person_id,),
                )

                naukri_records = cursor.fetchall()

                for record in naukri_records:

                    skills.extend(
                        extract_skills_from_record(record)
                    )

            except sqlite3.OperationalError:

                # If the source table is unavailable,
                # continue without failing the entire API.
                pass

            # =================================================
            # GIG WORKER RECORDS
            # =================================================

            try:

                cursor.execute(
                    """
                    SELECT *
                    FROM gig_workers
                    WHERE person_id = ?
                    """,
                    (person_id,),
                )

                gig_records = cursor.fetchall()

                for record in gig_records:

                    skills.extend(
                        extract_skills_from_record(record)
                    )

            except sqlite3.OperationalError:

                # If the source table is unavailable,
                # continue without failing the entire API.
                pass

            # ------------------------------------------------
            # Remove duplicate skills
            # ------------------------------------------------

            unique_skills = []

            seen = set()

            for skill in skills:

                if not isinstance(skill, str):
                    continue

                cleaned_skill = skill.strip()

                if not cleaned_skill:
                    continue

                skill_key = cleaned_skill.lower()

                if skill_key not in seen:

                    seen.add(skill_key)

                    unique_skills.append(
                        cleaned_skill
                    )

            # ------------------------------------------------
            # Build response
            # ------------------------------------------------

            results.append(
                {
                    "person_id": person_id,
                    "name": person["full_name"],
                    "email": person["email"],
                    "phone": person["phone"],
                    "city": person["city"],
                    "skills": unique_skills,
                    "skill_category": person["skill_category"],
                }
            )

        # ----------------------------------------------------
        # Return response
        # ----------------------------------------------------

        return {
            "count": len(results),
            "people": results,
        }

    finally:

        connection.close()


# ============================================================
# CATEGORY UPDATE MODEL
# ============================================================

class CategoryUpdate(BaseModel):

    category: str


# ============================================================
# UPDATE PERSON CATEGORY
# ============================================================

@app.put("/api/people/{person_id}/category")
def update_category(
    person_id: int,
    payload: CategoryUpdate,
):
    """
    Save the AI-generated skill category for a person.
    """

    allowed_categories = {
        "web dev",
        "data",
        "automation-heavy",
    }

    category = payload.category.strip().lower()

    # --------------------------------------------------------
    # Validate category
    # --------------------------------------------------------

    if category not in allowed_categories:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid category. Allowed categories: "
                "web dev, data, automation-heavy"
            ),
        )

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Check person exists
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT person_id
            FROM people
            WHERE person_id = ?
            """,
            (person_id,),
        )

        person = cursor.fetchone()

        if person is None:

            raise HTTPException(
                status_code=404,
                detail="Person not found.",
            )

        # ----------------------------------------------------
        # Update category
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE people
            SET skill_category = ?
            WHERE person_id = ?
            """,
            (
                category,
                person_id,
            ),
        )

        connection.commit()

        return {
            "success": True,
            "person_id": person_id,
            "skill_category": category,
        }

    finally:

        connection.close()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "database": str(DATABASE_FILE),
    }