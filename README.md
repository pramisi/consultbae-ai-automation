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
5. Production scaling plan

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
- Python `wave`
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

SQLite is used as the local database for the take-home implementation.

---

# 3. Project Structure

```text
consultbae-ai-automation/
│
├── api/
│   ├── server.py
│   └── audio.py
│
├── frontend/
│   └── index.html
│
├── audio/
│   └── submissions/
│       └── generated audio files
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
│   ├── inspect_database.py
│   ├── matching.py
│   └── merge_data.py
│
├── workflows/
│   └── task-2-skill-categorization.json
│
├── .gitignore
├── README.md
├── stuck_log.md
├── data_issues_report.md
├── TASK5_SCALE_PLAN.md
└── requirements.txt

## Tasks Overview

### Task 1 — Data Merge & Identity Resolution

Task 1 combines applicant and contact data from three source systems: Naukri applicants, Gig Workers, and CBNexus contacts.

The pipeline cleans and normalizes fields such as names, emails, phone numbers, cities, dates, and CTC values. It then uses conservative identity matching based primarily on normalized email and phone numbers, followed by name and city matching. Ambiguous matches are stored separately for manual review.

---

### Task 2 — AI Skill Categorization Automation

Task 2 uses an n8n workflow and an LLM to automatically categorize each person's technical skills into exactly one of three categories:

- `web dev`
- `data`
- `automation-heavy`

The workflow retrieves people from the backend API, processes each person's skills, validates the LLM response using JavaScript, and updates the person's category through an HTTP API request.

The workflow is stored in:

`workflows/task-2-skill-categorization.json`

---

### Task 3 — Mini Audio Collection App

Task 3 implements a web-based audio collection application using HTML, CSS, JavaScript, and FastAPI.

Users can enter their name and phone number and record audio through the browser. The recording is converted to WAV format and submitted to the backend.

For each submission, the application stores the recording and extracts:

- Duration
- Sample rate
- Bitrate
- Loudness

All submitted recordings are displayed in the frontend with an audio player and their extracted properties.

---

### Task 4 — Data Issues Report

Task 4 identifies and documents data-quality problems present in the three source datasets.

The analysis covers issues such as duplicate records, missing values, malformed rows, inconsistent phone numbers, city variations, mixed date formats, repeated headers, inconsistent status/verification values, and ambiguous identity matches.

The detailed findings and handling decisions are documented in:

`data_issues_report.md`

---

### Task 5 — Scaling Plan

Task 5 describes how the current prototype could be scaled to support approximately 5,000 workers over a single weekend.

The proposed production improvements include moving from SQLite to PostgreSQL, storing audio in object storage, using queue-based audio processing, horizontally scaling FastAPI servers, adding retries and idempotency, implementing pagination, and adding monitoring and backups.

The detailed production scaling plan is documented in:

`TASK5_SCALE_PLAN.md`


