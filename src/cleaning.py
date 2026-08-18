import re
from datetime import datetime


def clean_text(value):
    """Convert a value into clean text or None."""
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    if value.lower() in {"nan", "none", "null"}:
        return None

    return value


def normalize_email(value):
    """Normalize email for matching."""
    value = clean_text(value)

    if not value:
        return None

    return value.lower()


def normalize_name(value):
    """Normalize a person's name for matching."""
    value = clean_text(value)

    if not value:
        return None

    value = value.lower()

    # Remove punctuation
    value = re.sub(r"[^a-z0-9 ]+", " ", value)

    # Remove extra spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_phone(value):
    """
    Normalize Indian phone numbers.

    Examples:
        +91-9000000254 -> 9000000254
        919000000254   -> 9000000254
        09000000254    -> 9000000254
    """
    value = clean_text(value)

    if not value:
        return None

    digits = re.sub(r"\D", "", value)

    if not digits:
        return None

    # Remove India's country code
    if digits.startswith("91") and len(digits) >= 12:
        digits = digits[-10:]

    # Remove leading zero
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[-10:]

    if len(digits) >= 10:
        return digits[-10:]

    return digits


def normalize_city(value):
    """Normalize common city variations."""
    value = clean_text(value)

    if not value:
        return None

    value = value.lower()

    aliases = {
        "gurgaon": "gurugram",
        "gurugram": "gurugram",
        "new delhi": "delhi",
        "delhi ncr": "delhi",
        "delhi": "delhi",
        "bangalore": "bengaluru",
        "bengaluru": "bengaluru",
    }

    return aliases.get(value, value)


def parse_date(value):
    """
    Convert common date formats into YYYY-MM-DD.

    Returns None when the date cannot be parsed.
    """
    value = clean_text(value)

    if not value:
        return None

    formats = [
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d-%m-%y",
        "%d %b %Y",
        "%d %B %Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]

    for date_format in formats:
        try:
            parsed = datetime.strptime(value, date_format)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def parse_ctc(value):
    """
    Normalize CTC.

    Values below 100 are treated as lakh values.
    Larger values are treated as INR values.

    Examples:
        8.3     -> 830000
        11.2    -> 1120000
        417964  -> 417964
    """
    value = clean_text(value)

    if not value:
        return None

    value = value.lower()
    value = value.replace("₹", "")
    value = value.replace(",", "")
    value = value.replace("lpa", "")
    value = value.replace("lakh", "")
    value = value.strip()

    try:
        number = float(value)
    except ValueError:
        return None

    if number < 100:
        return int(number * 100000)

    return int(number)