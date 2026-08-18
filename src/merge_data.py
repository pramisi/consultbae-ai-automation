import csv
import json
from pathlib import Path

from .database import (
    get_connection,
    create_tables,
    clear_database,
)

from .cleaning import (
    clean_text,
    normalize_email,
    normalize_phone,
    normalize_city,
    parse_date,
    parse_ctc,
)

from .matching import find_match


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

NAUKRI_FILE = DATA_DIR / "source1_naukri_applicants.csv"
GIG_FILE = DATA_DIR / "source2_gig_workers.csv"
CBNEXUS_FILE = DATA_DIR / "source3_cbnexus_contacts.csv"


# ============================================================
# DATA QUALITY HELPERS
# ============================================================

def add_quality_issue(
    connection,
    source_name,
    source_row,
    issue_type,
    description,
    action_taken,
):
    """
    Store a data-quality issue in the database.
    """

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
    """
    Store uncertain identity matches for manual review.
    """

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


# ============================================================
# PERSON CREATION
# ============================================================

def create_person(
    connection,
    name,
    email=None,
    phone=None,
    city=None,
):
    """
    Create a new master person record.
    """

    cursor = connection.cursor()

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
            normalize_name_for_db(name),
            normalize_email(email),
            normalize_phone(phone),
            normalize_city(city),
        ),
    )

    connection.commit()

    return cursor.lastrowid


def normalize_name_for_db(value):
    """
    Normalize a person's name for storage.
    """

    from .cleaning import normalize_name

    return normalize_name(value)


# ============================================================
# FIND OR CREATE PERSON
# ============================================================

def find_or_create_person(
    connection,
    source_name,
    source_row,
    name,
    email=None,
    phone=None,
    city=None,
):
    """
    Try to match the source record to an existing person.

    If a safe match is found:
        return existing person_id

    Otherwise:
        create a new person.

    Uncertain matches are stored in match_reviews.
    """

    match = find_match(
        connection,
        name=name,
        email=email,
        phone=phone,
        city=city,
    )

    if match["person_id"] is not None:
        return match["person_id"]

    # No safe match found.
    # Create a new master person.

    person_id = create_person(
        connection,
        name=name,
        email=email,
        phone=phone,
        city=city,
    )

    # If the matching system had some evidence
    # but was not confident enough to merge,
    # store it for manual review.

    if match["confidence"] > 0:

        add_match_review(
            connection,
            source_name,
            source_row,
            name,
            email,
            phone,
            match["confidence"],
            match["reason"],
        )

    return person_id


# ============================================================
# NAUKRI
# ============================================================

def process_naukri(connection):

    print("\nProcessing Naukri applicants...")

    with open(
        NAUKRI_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for source_row, row in enumerate(reader, start=2):

            # ------------------------------------------------
            # Read raw fields
            # ------------------------------------------------

            name = clean_text(row.get("Full Name"))
            email = clean_text(row.get("Email"))
            phone = clean_text(row.get("Phone"))
            city = clean_text(row.get("City"))

            experience_raw = clean_text(
                row.get("Experience (Years)")
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

            # ------------------------------------------------
            # Blank row
            # ------------------------------------------------

            if not any(row.values()):

                add_quality_issue(
                    connection,
                    "naukri",
                    source_row,
                    "blank_row",
                    "Completely blank row found.",
                    "Skipped row.",
                )

                continue

            # ------------------------------------------------
            # Experience
            # ------------------------------------------------

            experience = None

            if experience_raw:

                try:
                    experience = float(experience_raw)

                except ValueError:

                    add_quality_issue(
                        connection,
                        "naukri",
                        source_row,
                        "invalid_experience",
                        f"Invalid experience: {experience_raw}",
                        "Stored as NULL.",
                    )

            # ------------------------------------------------
            # CTC
            # ------------------------------------------------

            ctc_inr = parse_ctc(ctc_raw)

            if ctc_raw:

                try:

                    numeric_ctc = float(
                        ctc_raw.replace(",", "")
                    )

                    if numeric_ctc < 100:

                        add_quality_issue(
                            connection,
                            "naukri",
                            source_row,
                            "ctc_in_lakhs",
                            (
                                f"CTC value '{ctc_raw}' "
                                "appears to be in lakhs."
                            ),
                            (
                                f"Converted to INR: "
                                f"{ctc_inr}"
                            ),
                        )

                except ValueError:

                    add_quality_issue(
                        connection,
                        "naukri",
                        source_row,
                        "invalid_ctc",
                        f"Invalid CTC value: {ctc_raw}",
                        "Stored normalized CTC as NULL.",
                    )

            # ------------------------------------------------
            # Application date
            # ------------------------------------------------

            applied_date = parse_date(
                applied_date_raw
            )

            if applied_date_raw and not applied_date:

                add_quality_issue(
                    connection,
                    "naukri",
                    source_row,
                    "invalid_date",
                    (
                        f"Could not parse date: "
                        f"{applied_date_raw}"
                    ),
                    "Stored normalized date as NULL.",
                )

            # ------------------------------------------------
            # Detect future dates
            # ------------------------------------------------

            if applied_date:

                if applied_date > "2026-08-18":

                    add_quality_issue(
                        connection,
                        "naukri",
                        source_row,
                        "future_date",
                        (
                            f"Application date "
                            f"{applied_date} is after "
                            "the assignment date."
                        ),
                        (
                            "Preserved the source value "
                            "and flagged it."
                        ),
                    )

            # ------------------------------------------------
            # Find or create master person
            # ------------------------------------------------

            person_id = find_or_create_person(
                connection,
                source_name="naukri",
                source_row=source_row,
                name=name,
                email=email,
                phone=phone,
                city=city,
            )

            # ------------------------------------------------
            # Convert skills to JSON
            # ------------------------------------------------

            skills_list = []

            if skills_raw:

                skills_list = [
                    skill.strip()
                    for skill in skills_raw.split(",")
                    if skill.strip()
                ]

            # ------------------------------------------------
            # Insert source record
            # ------------------------------------------------

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
                    json.dumps(skills_list),
                ),
            )

    connection.commit()

    print("Naukri processing complete.")


# ============================================================
# RATE PARSER
# ============================================================

def parse_rate(value):
    """
    Parse Gig Worker rates such as:

        1415/hr
        15k/month
        72k/month

    Returns:
        rate_value
        rate_unit
    """

    value = clean_text(value)

    if not value:
        return None, None

    value_lower = value.lower().strip()

    if "/" not in value_lower:
        return None, None

    number_part, unit = value_lower.split("/", 1)

    number_part = number_part.strip()
    unit = unit.strip()

    multiplier = 1

    if number_part.endswith("k"):

        multiplier = 1000
        number_part = number_part[:-1]

    try:

        number = float(number_part)

    except ValueError:

        return None, None

    return number * multiplier, unit


# ============================================================
# GIG WORKERS
# ============================================================

def process_gig_workers(connection):

    print("\nProcessing Gig Workers...")

    with open(
        GIG_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.reader(file)

        # Read the header
        header = next(reader)

        for source_row, values in enumerate(
            reader,
            start=2,
        ):

            # ------------------------------------------------
            # Completely blank row
            # ------------------------------------------------

            if not any(
                clean_text(value)
                for value in values
            ):

                add_quality_issue(
                    connection,
                    "gig_workers",
                    source_row,
                    "blank_row",
                    "Completely blank row found.",
                    "Skipped row.",
                )

                continue

            # ------------------------------------------------
            # Check column count
            # ------------------------------------------------

            if len(values) != 6:

                add_quality_issue(
                    connection,
                    "gig_workers",
                    source_row,
                    "wrong_column_count",
                    (
                        f"Expected 6 columns but "
                        f"found {len(values)}."
                    ),
                    "Skipped malformed row.",
                )

                continue

            # ------------------------------------------------
            # Read the six columns
            # ------------------------------------------------

            email = clean_text(values[0])
            name = clean_text(values[1])
            rate = clean_text(values[2])
            location = clean_text(values[3])
            status = clean_text(values[4])
            skill_tags = clean_text(values[5])

            # ------------------------------------------------
            # Detect shifted row
            # ------------------------------------------------
            #
            # Correct structure:
            #
            # email | worker_name | rate | location | status | skills
            #
            # Corrupted row:
            #
            # skills | email | name | rate | location | status
            #
            # Detection:
            #
            # 1. First value contains commas.
            # 2. Second value looks like an email.
            #
            # ------------------------------------------------

            shifted_row = (
                email
                and "," in email
                and name
                and "@" in name
            )

            if shifted_row:

                original_values = values.copy()

                # Repair the shifted row.

                skill_tags = original_values[0]
                email = original_values[1]
                name = original_values[2]
                rate = original_values[3]
                location = original_values[4]
                status = original_values[5]

                add_quality_issue(
                    connection,
                    "gig_workers",
                    source_row,
                    "shifted_columns",
                    (
                        "Row was shifted: skill tags "
                        "were found in the email column "
                        "and the email was found in the "
                        "worker name column."
                    ),
                    "Detected the pattern and repaired the row.",
                )

            # ------------------------------------------------
            # Detect duplicate source record
            # ------------------------------------------------

            normalized_email = normalize_email(email)

            duplicate_found = False

            if normalized_email:

                cursor = connection.cursor()

                cursor.execute(
                    """
                    SELECT email_raw
                    FROM gig_workers
                    WHERE email_raw IS NOT NULL
                    """
                )

                existing_records = cursor.fetchall()

                for existing in existing_records:

                    existing_email = normalize_email(
                        existing["email_raw"]
                    )

                    if existing_email == normalized_email:

                        duplicate_found = True
                        break

            if duplicate_found:

                add_quality_issue(
                    connection,
                    "gig_workers",
                    source_row,
                    "duplicate_record",
                    (
                        "A Gig Worker record with the "
                        "same normalized email already "
                        "exists."
                    ),
                    (
                        "Kept the source row for traceability "
                        "and linked it to the same master person."
                    ),
                )

            # ------------------------------------------------
            # Parse rate
            # ------------------------------------------------

            rate_value, rate_unit = parse_rate(rate)

            if rate and rate_value is None:

                add_quality_issue(
                    connection,
                    "gig_workers",
                    source_row,
                    "invalid_rate",
                    f"Could not parse rate: {rate}",
                    "Stored parsed rate as NULL.",
                )

            # ------------------------------------------------
            # Find or create master person
            # ------------------------------------------------

            person_id = find_or_create_person(
                connection,
                source_name="gig_workers",
                source_row=source_row,
                name=name,
                email=email,
                phone=None,
                city=location,
            )

            # ------------------------------------------------
            # Convert skills into JSON
            # ------------------------------------------------

            skill_list = []

            if skill_tags:

                skill_list = [
                    skill.strip()
                    for skill in skill_tags.split(",")
                    if skill.strip()
                ]

            # ------------------------------------------------
            # Insert Gig Worker record
            # ------------------------------------------------

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO gig_workers (
                    person_id,
                    source_row,
                    email_raw,
                    worker_name_raw,
                    rate_raw,
                    rate_value,
                    rate_unit,
                    location_raw,
                    status_raw,
                    skill_tags_raw,
                    skill_tags_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_id,
                    source_row,
                    email,
                    name,
                    rate,
                    rate_value,
                    rate_unit,
                    location,
                    status,
                    skill_tags,
                    json.dumps(skill_list),
                ),
            )

    connection.commit()

    print("Gig Workers processing complete.")


# ============================================================
# CBNEXUS
# ============================================================

def process_cbnexus(connection):

    print("\nProcessing CBNexus contacts...")

    with open(
        CBNEXUS_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for source_row, row in enumerate(
            reader,
            start=2,
        ):

            name = clean_text(
                row.get("Name")
            )

            phone = clean_text(
                row.get("Phone Number")
            )

            city = clean_text(
                row.get("City")
            )

            verified_raw = clean_text(
                row.get("Verified")
            )

            projects_raw = clean_text(
                row.get("Projects Completed")
            )

            # ------------------------------------------------
            # Detect repeated header
            # ------------------------------------------------

            if (
                name == "Name"
                and phone == "Phone Number"
            ):

                add_quality_issue(
                    connection,
                    "cbnexus",
                    source_row,
                    "repeated_header",
                    "Header row appeared inside the data.",
                    "Skipped repeated header.",
                )

                continue

            # ------------------------------------------------
            # Projects completed
            # ------------------------------------------------

            projects_completed = None

            if projects_raw:

                try:

                    projects_completed = int(
                        projects_raw
                    )

                except ValueError:

                    add_quality_issue(
                        connection,
                        "cbnexus",
                        source_row,
                        "invalid_projects",
                        (
                            "Invalid projects completed "
                            f"value: {projects_raw}"
                        ),
                        "Stored as NULL.",
                    )

            # ------------------------------------------------
            # Verified
            # ------------------------------------------------

            verified = None

            if verified_raw:

                value = verified_raw.lower()

                if value in {
                    "y",
                    "yes",
                    "true",
                    "1",
                }:

                    verified = 1

                elif value in {
                    "n",
                    "no",
                    "false",
                    "0",
                }:

                    verified = 0

                else:

                    add_quality_issue(
                        connection,
                        "cbnexus",
                        source_row,
                        "invalid_verified",
                        (
                            f"Unknown verification "
                            f"value: {verified_raw}"
                        ),
                        "Stored as NULL.",
                    )

            # ------------------------------------------------
            # Find or create person
            # ------------------------------------------------

            person_id = find_or_create_person(
                connection,
                source_name="cbnexus",
                source_row=source_row,
                name=name,
                phone=phone,
                city=city,
            )

            # ------------------------------------------------
            # Insert CBNexus record
            # ------------------------------------------------

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO cbnexus_contacts (
                    person_id,
                    source_row,
                    name_raw,
                    phone_raw,
                    city_raw,
                    verified_raw,
                    verified,
                    projects_completed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_id,
                    source_row,
                    name,
                    phone,
                    city,
                    verified_raw,
                    verified,
                    projects_completed,
                ),
            )

    connection.commit()

    print("CBNexus processing complete.")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 60)
    print("CONSULTBAE DATA MERGE PIPELINE")
    print("=" * 60)

    connection = get_connection()

    try:

        # ----------------------------------------------------
        # Create tables
        # ----------------------------------------------------

        create_tables(connection)

        # ----------------------------------------------------
        # Start with a clean generated database
        # ----------------------------------------------------

        clear_database(connection)

        # ----------------------------------------------------
        # Process all three sources
        # ----------------------------------------------------

        process_naukri(connection)

        process_gig_workers(connection)

        process_cbnexus(connection)

        # ----------------------------------------------------
        # Final statistics
        # ----------------------------------------------------

        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM people"
        )

        people_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM naukri_applicants"
        )

        naukri_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM gig_workers"
        )

        gig_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM cbnexus_contacts"
        )

        cbnexus_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM data_quality_issues"
        )

        issue_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM match_reviews"
        )

        review_count = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Display results
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)

        print(
            f"Master people:       {people_count}"
        )

        print(
            f"Naukri records:      {naukri_count}"
        )

        print(
            f"Gig worker records:   {gig_count}"
        )

        print(
            f"CBNexus records:      {cbnexus_count}"
        )

        print(
            f"Quality issues:       {issue_count}"
        )

        print(
            f"Match reviews:        {review_count}"
        )

        print("=" * 60)

    finally:

        connection.close()


if __name__ == "__main__":
    main()