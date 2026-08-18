# ConsultBae AI Automation

A Python-based data ingestion, cleaning, normalization, and identity-resolution pipeline for combining applicant and contact information from multiple source systems.

The project processes three source datasets:

- Naukri applicants
- Gig Workers
- CBNexus contacts

The pipeline cleans inconsistent data, detects data-quality issues, matches records belonging to the same person, creates a master `people` table, and stores uncertain matches separately for manual review.

---

# 1. Project Objective

The goal of the pipeline is to create a unified view of people across multiple source systems.

The same person may appear in more than one source with:

- Different capitalization
- Different phone-number formats
- Different email capitalization
- Different city formatting
- Duplicate records
- Malformed rows
- Ambiguous identity information

The pipeline therefore separates:

1. Source records
2. Master identities
3. Data-quality issues
4. Uncertain identity matches

---

# 2. Technologies Used

- Python
- SQLite
- CSV
- Git
- GitHub

Python is used for:

- CSV ingestion
- Data cleaning
- Normalization
- Identity matching
- Data-quality detection
- Database loading
- Validation

SQLite is used as the local database.

---

# 3. Project Structure

```text
consultbae-ai-automation/
│
├── data/
│   ├── source1_naukri_applicants.csv
│   ├── source2_gig_workers.csv
│   └── source3_cbnexus_contacts.csv
│
├── src/
│   ├── __init__.py
│   ├── cleaning.py
│   ├── database.py
│   ├── matching.py
│   ├── merge_data.py
│   └── inspect_database.py
│
├── .gitignore
├── README.md
├── stuck_log.md
└── consultbae.db