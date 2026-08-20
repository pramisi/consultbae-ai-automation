Task 4 — Data Issues Report

Overview

I reviewed all three source CSV files used by the merge pipeline:

source1_naukri_applicants.csv — 42 rows

source2_gig_workers.csv — 32 rows

source3_cbnexus_contacts.csv — 31 rows

The datasets contain intentionally inconsistent formatting, duplicate records, malformed rows, and ambiguous identity information. The issues below are separated into data-quality problems and identity-resolution risks.

1. source1_naukri_applicants.csv

1.1 Duplicate applicant records

Two duplicate/near-duplicate identities appear in the Naukri data.

Rohit Verma

R. Verma and Rohit Verma

Same email: rohit.verma13@mailtest.example.org

Same phone: 9000000294

Same city, experience, CTC, date, and skills

Nikhil Chopra

Appears twice with the same name and phone: 9000000103

One record uses alt.nikhil.chopra70@example.com

The other uses nikhil.chopra70@example.com

The remaining applicant fields are identical

Handling: normalize names/emails/phones and treat strong exact identifiers as evidence that these records belong to the same person. Keep provenance instead of silently discarding source records.

1.2 Mixed phone-number formats

Phone numbers are stored in different forms:

9000000237

919000000254

919000000288

The 91 country code is sometimes included and sometimes omitted.

Handling: normalize phone numbers to a consistent 10-digit representation before identity matching.

1.3 Inconsistent city formatting

Examples include:

PUNE, pune, Pune

NOIDA, Noida, Noida 

GURGAON, Gurgaon

gurugram , Gurugram

Bangalore, bangalore, Bengaluru

new delhi, New Delhi

Delhi NCR

There are both capitalization/whitespace differences and genuine aliases.

Handling: trim whitespace and normalize case. Where appropriate, map known aliases such as Bangalore/Bengaluru and Gurgaon/Gurugram to a canonical city.

1.4 Inconsistent date formats

Applied Date appears in several formats, including:

2026-08-08

24-07-2026

07/13/2026

7 Jul 2026

19 Jul 2026

Handling: parse multiple accepted input formats and store dates in one canonical database format such as ISO YYYY-MM-DD.

1.5 Inconsistent CTC units/types

Most Current CTC values look like annual numeric amounts, for example 417964 or 775670, while some rows contain small values such as:

Amit Agarwal: 4.2

Shreya Gupta: 8.3

Nikhil Malhotra: 5.1

Ritu Sharma: 6.1

Meera Bhatia: 11.2

These appear to represent a different unit/scale, likely lakhs, compared with the larger numeric values.

Handling: detect the mixed scale rather than treating every number as the same unit. Preserve the raw value and normalize only when the intended unit can be established.

1.6 Future application dates

Relative to the dataset review date of 20 August 2026, these records contain future dates:

Nikhil Malhotra — 21-08-2026

Arjun Mishra — 22-08-2026

Isha Kapoor — 08/21/2026

Handling: flag future dates as a data-quality issue instead of silently changing them. They may be valid scheduled applications, but they should be reviewed.

2. source2_gig_workers.csv

2.1 Completely blank row

One row contains no values in any column.

Handling: detect and reject/skip completely empty records during ingestion while recording the issue.

2.2 Malformed / shifted row

One row is structurally corrupted:

email_id contains react, javascript, mysql

worker_name contains an email address

rate contains Isha Chopra

location contains 1406/hr

status contains Pune

skill_tags contains active

The fields are shifted relative to the expected schema.

Handling: validate the row against expected column types/patterns. Do not load it as a normal worker record. Record it as a malformed-row data-quality issue.

2.3 Mixed rate units

The rate field mixes:

hourly rates such as 1415/hr, 843/hr

monthly rates such as 15k/month, 72k/month, 79k/month

There are 16 /hr values and 14 /month values among non-empty rows.

Handling: preserve the original rate and unit separately. Do not compare hourly and monthly values directly without a business rule for conversion.

2.4 Inconsistent status capitalization

Examples:

Active

ACTIVE

active

Inactive

INACTIVE-style variations

The malformed row also has Pune in the status column.

Handling: normalize valid statuses to a controlled vocabulary such as active, inactive, and paused. Reject values that do not belong to the vocabulary.

2.5 Inconsistent email capitalization

Example:

ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG

while other records use lowercase.

Handling: lowercase emails before matching and uniqueness checks.

2.6 Inconsistent location formatting

Examples include:

Pune, PUNE, pune

Gurgaon, gurugram

Bengaluru, bangalore

New Delhi, new delhi

Handling: trim and canonicalize locations before matching.

3. source3_cbnexus_contacts.csv

3.1 Repeated header row inside the data

Row 15 contains:

Name

Phone Number

City

Verified

Projects Completed

These are column headers rather than a real contact record.

Handling: detect and remove repeated header rows during ingestion, while recording the issue.

3.2 Inconsistent verification values

The Verified field uses several representations:

Y

Yes

yes

No

N

Verified (from the repeated header row)

Handling: map valid values to a boolean representation such as true/false and reject the header value.

3.3 Mixed phone-number formats

Examples include:

9000000268

919000000231

+91-9000000131

Handling: strip formatting and country-code variations and normalize to a consistent 10-digit phone number.

3.4 Inconsistent city formatting

Examples include:

Pune, PUNE, pune

Noida, NOIDA, Noida 

New Delhi, new delhi

Gurgaon, gurugram

Bengaluru

Delhi NCR

Handling: trim, lowercase for matching, and map known aliases to canonical city names.

3.5 Same name with conflicting phone numbers

Arjun Mehta appears twice:

+91-9000000131

9000000272

Both are in Noida, but the phone numbers differ.

The first phone matches the Naukri record for Arjun Mehta, while the second does not.

Handling: do not merge solely on name. Treat the second record as an identity-resolution ambiguity and retain it for review unless another strong identifier confirms the match.

4. Cross-source Identity Resolution Issues

The biggest risk is assuming that names alone identify people.

Examples of useful matching evidence include:

normalized email

normalized phone

normalized name

city

supporting attributes

Strong cross-source matches

Examples:

Rohit Nair — Naukri phone 919000000268 matches CBNexus phone 9000000268

Priya Singh — Naukri phone 9000000287 matches CBNexus phone 9000000287

Tanvi Gupta — Naukri phone 919000000254 matches CBNexus phone 9000000254

Karan Bhatia — Naukri phone 919000000211 matches CBNexus phone 9000000211

Arjun Mehta — Naukri phone 9000000131 matches one CBNexus Arjun Mehta record

Shreya Gupta — Naukri phone 9000000227 matches CBNexus phone +91-9000000227

These demonstrate why phone normalization is important.

Ambiguous matches

The Arjun Mehta duplicate in CBNexus demonstrates that the same name can refer to different records. A matching system should therefore use multiple fields and avoid blindly merging same-name records.

5. General Handling Strategy

The pipeline should follow this order:

Preserve raw source data

Remove completely blank rows

Detect repeated headers

Validate row structure

Normalize names

Normalize emails

Normalize phone numbers

Normalize city/location values

Parse dates into a canonical format

Normalize categorical values such as status and verification

Detect duplicate records

Perform identity matching using strong identifiers first

Send uncertain matches to a manual-review table

Load clean records into the master database

Keep a data-quality/issues table for auditability

6. Key Lessons

The most important problems were not syntax errors but silent data inconsistencies:

the same phone can appear with different country-code formats

the same city can have multiple spellings/capitalization styles

rates can use different units

dates can use different formats

duplicate records can contain alternate emails

malformed rows can shift values into the wrong columns

repeated headers can look like real records

names alone are not reliable identifiers

The pipeline therefore validates and normalizes data before identity resolution instead of relying on exact string equality.