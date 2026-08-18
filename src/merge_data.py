import csv
import json
import sqlite3
from pathlib import Path

from .database import (
    get_connection,
    create_tables,
    clear_database,
)

from .cleaning import (
    clean_text,
    normalize_email,
    normalize_name,
    normalize_phone,
    normalize_city,
    parse_date,
    parse_ctc,
)

from .matching import find_match


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


NAUKRI_FILE = DATA_DIR / "source1_naukri_applicants.csv"
GIG_FILE = DATA_DIR / "source2_gig_workers.csv"
CBNEXUS_FILE = DATA_DIR / "source3_cbnexus_contacts.csv"

def add_quality_issue(
    connection,
    source_name,
    source_row,
    issue_type,
    description,
    action_taken,
):
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO data_quality_issues (
            source_name,
            source_row,
            issue_type,
            description,
            action_taken
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            source_name,
            source_row,
            issue_type,
            description,
            action_taken,
        ),
    )


def add_match_review(
    connection,
    source_name,
    source_row,
    name,
    email,
    phone,
    confidence,
    reason,
):
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO match_reviews (
            source_name,
            source_row,
            source_name_value,
            source_email,
            source_phone,
            confidence,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_name,
            source_row,
            name,
            email,
            phone,
            confidence,
            reason,
        ),
    )


def create_person(
    connection,
    name,
    email=None,
    phone=None,
    city=None,
):
    cursor = connection.cursor()

    normalized_name_value = normalize_name(name)
    normalized_email = normalize_email(email)
    normalized_phone = normalize_phone(phone)
    normalized_city = normalize_city(city)

    cursor.execute(
        """
        INSERT INTO people (
            full_name,
            normalized_name,
            email,
            phone,
            city
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            clean_text(name),
            normalized_name_value,
            normalized_email,
            normalized_phone,
            normalized_city,
        ),
    )

    connection.commit()

    return cursor.lastrowid

def process_naukri(connection):

    print("Processing Naukri applicants...")

    with open(
        NAUKRI_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for source_row, row in enumerate(reader, start=2):

            name = clean_text(row.get("Name"))
            email = clean_text(row.get("Email"))
            phone = clean_text(row.get("Phone"))
            city = clean_text(row.get("City"))

            # ----------------------------------------
            # Validate basic row
            # ----------------------------------------

            if not any(row.values()):

                add_quality_issue(
                    connection,
                    "naukri",
                    source_row,
                    "blank_row",
                    "Completely blank row found.",
                    "Skipped blank row.",
                )

                continue

            # ----------------------------------------
            # Normalize fields
            # ----------------------------------------

            normalized_email = normalize_email(email)
            normalized_phone = normalize_phone(phone)
            normalized_city = normalize_city(city)

            experience_raw = clean_text(
                row.get("Experience")
            )

            ctc_raw = clean_text(
                row.get("Current CTC")
            )

            applied_date_raw = clean_text(
                row.get("Applied Date")
            )

            skills_raw = clean_text(
                row.get("Skills")
            )

            # ----------------------------------------
            # Parse experience
            # ----------------------------------------

            try:
                experience = (
                    float(experience_raw)
                    if experience_raw
                    else None
                )
            except ValueError:

                experience = None

                add_quality_issue(
                    connection,
                    "naukri",
                    source_row,
                    "invalid_experience",
                    f"Invalid experience value: {experience_raw}",
                    "Stored as NULL.",
                )

            # ----------------------------------------
            # Parse CTC
            # ----------------------------------------

            ctc_inr = parse_ctc(ctc_raw)

            if ctc_raw and ctc_inr is not None:

                try:
                    numeric_ctc = float(
                        ctc_raw.replace(",", "")
                    )

                    if numeric_ctc < 100:

                        add_quality_issue(
                            connection,
                            "naukri",
                            source_row,
                            "ctc_unit",
                            f"CTC appears to be in lakhs: {ctc_raw}",
                            f"Converted to INR: {ctc_inr}",
                        )

                except ValueError:
                    pass

            # ----------------------------------------
            # Parse date
            # ----------------------------------------

            applied_date = parse_date(
                applied_date_raw
            )

            if applied_date_raw and not applied_date:

                add_quality_issue(
                    connection,
                    "naukri",
                    source_row,
                    "invalid_date",
                    f"Could not parse date: {applied_date_raw}",
                    "Stored normalized date as NULL.",
                )

            # ----------------------------------------
            # Find existing person
            # ----------------------------------------

            match = find_match(
                connection,
                name=name,
                email=email,
                phone=phone,
                city=city,
            )

            if match["person_id"]:

                person_id = match["person_id"]

            else:

                person_id = create_person(
                    connection,
                    name=name,
                    email=email,
                    phone=phone,
                    city=city,
                )

                if match["confidence"] > 0:

                    add_match_review(
                        connection,
                        "naukri",
                        source_row,
                        name,
                        email,
                        phone,
                        match["confidence"],
                        match["reason"],
                    )

            # ----------------------------------------
            # Store source record
            # ----------------------------------------

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO naukri_applicants (
                    person_id,
                    source_row,
                    full_name_raw,
                    email_raw,
                    phone_raw,
                    city_raw,
                    experience_years,
                    current_ctc_raw,
                    current_ctc_inr,
                    applied_date_raw,
                    applied_date,
                    skills_raw,
                    skills_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_id,
                    source_row,
                    name,
                    email,
                    phone,
                    city,
                    experience,
                    ctc_raw,
                    ctc_inr,
                    applied_date_raw,
                    applied_date,
                    skills_raw,
                    json.dumps(
                        [
                            skill.strip()
                            for skill in skills_raw.split(",")
                        ]
                    )
                    if skills_raw
                    else "[]",
                ),
            )

    connection.commit()

    print("Naukri processing complete.")