from .database import get_connection


def main():

    connection = get_connection()
    cursor = connection.cursor()

    print("\n" + "=" * 60)
    print("DATABASE INSPECTION")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Count master people
    # --------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total_people
        FROM people
    """)

    total_people = cursor.fetchone()["total_people"]

    print(f"\nTotal master people: {total_people}")

    # --------------------------------------------------
    # 2. Check duplicate emails
    # --------------------------------------------------

    print("\n" + "-" * 60)
    print("DUPLICATE EMAILS")
    print("-" * 60)

    cursor.execute("""
        SELECT
            email,
            COUNT(*) AS count
        FROM people
        WHERE email IS NOT NULL
        GROUP BY email
        HAVING COUNT(*) > 1
    """)

    duplicate_emails = cursor.fetchall()

    if not duplicate_emails:

        print("No duplicate emails found.")

    else:

        for row in duplicate_emails:

            print(
                f"{row['email']} -> "
                f"{row['count']} records"
            )

    # --------------------------------------------------
    # 3. Check duplicate phones
    # --------------------------------------------------

    print("\n" + "-" * 60)
    print("DUPLICATE PHONES")
    print("-" * 60)

    cursor.execute("""
        SELECT
            phone,
            COUNT(*) AS count
        FROM people
        WHERE phone IS NOT NULL
        GROUP BY phone
        HAVING COUNT(*) > 1
    """)

    duplicate_phones = cursor.fetchall()

    if not duplicate_phones:

        print("No duplicate phones found.")

    else:

        for row in duplicate_phones:

            print(
                f"{row['phone']} -> "
                f"{row['count']} records"
            )

    # --------------------------------------------------
    # 4. Match reviews
    # --------------------------------------------------

    print("\n" + "-" * 60)
    print("MATCH REVIEWS")
    print("-" * 60)

    cursor.execute("""
        SELECT
            review_id,
            source_name,
            source_row,
            source_name_value,
            source_email,
            source_phone,
            confidence,
            reason
        FROM match_reviews
        ORDER BY review_id
    """)

    reviews = cursor.fetchall()

    if not reviews:

        print("No match reviews.")

    else:

        for row in reviews:

            print(
                f"\nReview #{row['review_id']}"
            )

            print(
                f"Source: {row['source_name']}"
            )

            print(
                f"Row: {row['source_row']}"
            )

            print(
                f"Name: {row['source_name_value']}"
            )

            print(
                f"Email: {row['source_email']}"
            )

            print(
                f"Phone: {row['source_phone']}"
            )

            print(
                f"Confidence: {row['confidence']}"
            )

            print(
                f"Reason: {row['reason']}"
            )

    # --------------------------------------------------
    # 5. Cross-source people
    # --------------------------------------------------

    print("\n" + "-" * 60)
    print("PEOPLE FOUND IN MULTIPLE SYSTEMS")
    print("-" * 60)

    cursor.execute("""
        SELECT
            p.person_id,
            p.full_name,

            COUNT(DISTINCT n.id)
                AS naukri_records,

            COUNT(DISTINCT g.id)
                AS gig_records,

            COUNT(DISTINCT c.id)
                AS cbnexus_records

        FROM people p

        LEFT JOIN naukri_applicants n
            ON p.person_id = n.person_id

        LEFT JOIN gig_workers g
            ON p.person_id = g.person_id

        LEFT JOIN cbnexus_contacts c
            ON p.person_id = c.person_id

        GROUP BY
            p.person_id,
            p.full_name

        HAVING
            (
                CASE
                    WHEN COUNT(DISTINCT n.id) > 0
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN COUNT(DISTINCT g.id) > 0
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN COUNT(DISTINCT c.id) > 0
                    THEN 1
                    ELSE 0
                END
            ) >= 2

        ORDER BY p.full_name
    """)

    cross_source_people = cursor.fetchall()

    for row in cross_source_people:

        print(
            f"{row['person_id']:>3} | "
            f"{row['full_name']:<25} | "
            f"Naukri: {row['naukri_records']} | "
            f"Gig: {row['gig_records']} | "
            f"CBNexus: {row['cbnexus_records']}"
        )

        # --------------------------------------------------
    # 6. Check records without person_id
    # --------------------------------------------------

    print("\n" + "-" * 60)
    print("RECORDS WITHOUT PERSON ID")
    print("-" * 60)

    source_tables = [
        "naukri_applicants",
        "gig_workers",
        "cbnexus_contacts",
    ]

    for table in source_tables:

        cursor.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM {table}
            WHERE person_id IS NULL
            """
        )

        count = cursor.fetchone()["count"]

        print(
            f"{table}: {count} records without person_id"
        )

    # --------------------------------------------------
    # 7. Source record counts
    # --------------------------------------------------

    print("\n" + "-" * 60)
    print("SOURCE RECORD COUNTS")
    print("-" * 60)

    for table in source_tables:

        cursor.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM {table}
            """
        )

        count = cursor.fetchone()["count"]

        print(
            f"{table}: {count}"
        )

        # --------------------------------------------------
    # 8. Data quality issues
    # --------------------------------------------------

    print("\n" + "-" * 60)
    print("DATA QUALITY ISSUES")
    print("-" * 60)

    cursor.execute("""
        SELECT
            source_name,
            issue_type,
            COUNT(*) AS count
        FROM data_quality_issues
        GROUP BY
            source_name,
            issue_type
        ORDER BY
            source_name,
            issue_type
    """)

    issue_summary = cursor.fetchall()

    for row in issue_summary:

        print(
            f"{row['source_name']:<15} | "
            f"{row['issue_type']:<25} | "
            f"{row['count']}"
        )

    print("\n" + "=" * 60)

    connection.close()


if __name__ == "__main__":
    main()