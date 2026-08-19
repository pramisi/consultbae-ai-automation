# ConsultBae AI Automation

A Python-based data ingestion, cleaning, normalization, identity-resolution, AI categorization, and audio collection application built for the ConsultBae AI Automation take-home assignment.

The project combines data from multiple source systems, resolves duplicate people, identifies data-quality issues, categorizes technical skills using an LLM through n8n, and provides a mini audio collection application for collecting worker recordings and extracting technical audio properties.

---

# 1. Project Objective

The goal of the project is to merge information from multiple source systems into a unified database and build automation on top of the resulting data.

The project contains the following major components:

1. Data ingestion and identity resolution
2. AI-based skill categorization
3. Mini audio collection application
4. Data-quality analysis and reporting

The same person may appear in multiple source systems with inconsistent information such as:

- Different capitalization
- Different phone-number formats
- Different email capitalization
- Different city formatting
- Duplicate records
- Missing values
- Malformed rows
- Ambiguous identity information

The pipeline therefore separates:

1. Source records
2. Master identities
3. Data-quality issues
4. Uncertain identity matches

---

# 2. Technologies Used

## Backend

- Python
- FastAPI
- SQLite
- CSV
- `wave`
- Git
- GitHub

## Frontend

- HTML
- CSS
- JavaScript
- Browser MediaRecorder API
- HTML5 Audio

## Automation

- n8n
- LLM
- HTTP API integration

Python is used for:

- CSV ingestion
- Data cleaning
- Normalization
- Identity matching
- Data-quality detection
- Database operations
- Audio processing
- Audio metadata extraction

SQLite is used as the local database.

---

# 3. Project Structure

```text
consultbae-ai-automation/
│
├── api/
│   ├── __init__.py
│   ├── server.py
│   ├── audio.py
│   └── ...
│
├── frontend/
│   └── index.html
│
├── audio/
│   └── submissions/
│       └── (generated audio files - ignored by Git)
│
├── data/
│   ├── source1_naukri_applicants.csv
│   ├── source2_gig_workers.csv
│   └── source3_cbnexus_contacts.csv
│
├── .gitignore
├── README.md
├── stuck_log.md
└── ...