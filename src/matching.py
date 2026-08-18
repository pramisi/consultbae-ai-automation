from .cleaning import (
    normalize_email,
    normalize_name,
    normalize_phone,
    normalize_city,
)


def get_all_people(connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            person_id,
            full_name,
            normalized_name,
            email,
            phone,
            city
        FROM people
    """)

    return cursor.fetchall()


def find_match(
    connection,
    name,
    email=None,
    phone=None,
    city=None,
):
    """
    Find an existing person using a conservative
    identity-matching strategy.

    Priority:
        1. Exact normalized email
        2. Exact normalized phone
        3. Exact name + city
        4. Otherwise manual review
    """

    normalized_email = normalize_email(email)
    normalized_phone = normalize_phone(phone)
    normalized_name_value = normalize_name(name)
    normalized_city_value = normalize_city(city)

    people = get_all_people(connection)

    # ------------------------------------------------
    # RULE 1: Exact email
    # ------------------------------------------------

    if normalized_email:

        for person in people:

            if person["email"] == normalized_email:

                return {
                    "person_id": person["person_id"],
                    "confidence": 100,
                    "reason": "exact email match",
                }

    # ------------------------------------------------
    # RULE 2: Exact phone
    # ------------------------------------------------

    if normalized_phone:

        for person in people:

            if person["phone"] == normalized_phone:

                return {
                    "person_id": person["person_id"],
                    "confidence": 100,
                    "reason": "exact phone match",
                }

    # ------------------------------------------------
    # RULE 3: Exact name + city
    # ------------------------------------------------

    candidates = []

    for person in people:

        if (
            person["normalized_name"] == normalized_name_value
            and person["city"] == normalized_city_value
        ):
            candidates.append(person)

    if len(candidates) == 1:

        person = candidates[0]

        email_conflict = (
            normalized_email
            and person["email"]
            and normalized_email != person["email"]
        )

        phone_conflict = (
            normalized_phone
            and person["phone"]
            and normalized_phone != person["phone"]
        )

        # Do not merge if a strong identifier conflicts.
        if email_conflict or phone_conflict:

            return {
                "person_id": None,
                "confidence": 60,
                "reason": (
                    "name + city matched, "
                    "but strong identifier conflicts"
                ),
            }

        return {
            "person_id": person["person_id"],
            "confidence": 85,
            "reason": "exact name + city match",
        }

    # ------------------------------------------------
    # RULE 4: Name only
    # ------------------------------------------------

    name_candidates = []

    for person in people:

        if person["normalized_name"] == normalized_name_value:
            name_candidates.append(person)

    if len(name_candidates) == 1:

        return {
            "person_id": None,
            "confidence": 55,
            "reason": (
                "unique name match only; "
                "manual review required"
            ),
        }

    if len(name_candidates) > 1:

        return {
            "person_id": None,
            "confidence": 50,
            "reason": (
                "multiple people share the same name; "
                "manual review required"
            ),
        }

    # ------------------------------------------------
    # No match
    # ------------------------------------------------

    return {
        "person_id": None,
        "confidence": 0,
        "reason": "no reliable match",
    }