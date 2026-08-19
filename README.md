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
---

# 4. Task 2 — AI Skill Categorization Automation

Task 2 implements an n8n workflow that automatically categorizes each person's technical skills using an LLM.

The workflow takes people from the API/database, processes their skills, assigns exactly one category, and updates the person's category through the API.

## Categories

Each person is assigned exactly one of the following categories:

- `web dev`
- `data`
- `automation-heavy`

## Workflow

The n8n workflow performs the following steps:

1. **Manual Trigger**
   - Starts the workflow manually from n8n.

2. **Get People**
   - Retrieves people records from the backend API.

3. **Split People**
   - Processes the people records individually.

4. **Code in JavaScript**
   - Prepares the skill data for categorization.

5. **Basic LLM Chain**
   - Sends the person's skills to an LLM.
   - The model determines the most appropriate category.

6. **JavaScript Categorization**
   - Validates and normalizes the LLM response.
   - Ensures that the result matches one of the allowed categories.

7. **HTTP Request**
   - Sends a `PUT` request to the backend API.
   - Updates the person's `category` field.

## LLM Categorization Logic

The LLM classifies skills according to their dominant technical area.

### Web Development

Examples include:

- React
- JavaScript
- FastAPI
- REST APIs
- Docker
- HTML/CSS

### Data

Examples include:

- SQL
- MySQL
- MongoDB
- Pandas
- NumPy
- Python when primarily used for data-related work

### Automation-Heavy

Examples include:

- n8n
- Zapier
- Selenium
- Web Scraping
- LangChain
- Workflow automation tools

When skills overlap multiple categories, the workflow uses the dominant skill group to determine the final category.

## Output

For every person, the workflow produces a category and updates the backend.

Example:

```json
{
  "success": true,
  "person_id": 1,
  "skill_category": "automation-heavy"
}