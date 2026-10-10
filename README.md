# Bulk Certificate Generator 📜

A Python backend API that takes a list of participants from an event or course and automatically generates PDF certificates for all of them.

---

## 💡 What Does This Project Do?

When an organization hosts a webinar, course, or hackathon, generating certificates one-by-one by hand is tedious. 

This project solves that by providing a REST API where you can:
1. Send a list of recipient names and details in one single request.
2. The server generates professional PDF certificates in the background.
3. If one recipient has invalid information (like an empty name), it marks only that certificate as failed and continues generating all the others.
4. You can check the progress of the batch and download the generated certificates individually or all together as a `.zip` file.

---

## 🛠️ Tech Stack

- **Language:** Python
- **API Framework:** FastAPI (fast, easy to use, comes with interactive web docs)
- **Database:** SQLite with SQLAlchemy (saves jobs and certificate records)
- **PDF Generation:** ReportLab (creates clean, vector PDF certificates)
- **Testing:** Pytest (verifies that everything works properly)

---

## 🚀 Getting Started (Setup & Run)

Follow these simple steps to run the project on your machine:

### Step 1: Clone the Repository
```bash
git clone https://github.com/prannoydidymus/Bulk-Certificate-Generator.git
cd Bulk-Certificate-Generator
```

### Step 2: Create and Activate a Virtual Environment
- **On Windows:**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **On Mac / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Step 3: Install Required Packages
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python run.py
```

The server will start at: **`http://127.0.0.1:8000`**

You can open the interactive API docs directly in your browser at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 📖 How to Use the API

### 1. Submit a Certificate Generation Request

You can test this easily using the Swagger UI at `http://127.0.0.1:8000/docs` or using `curl`:

**Endpoint:** `POST /api/v1/jobs`

**Request Body Example:**
```json
{
  "event_name": "Python for Beginners Workshop",
  "organization_name": "Code Academy",
  "issue_date": "October 10, 2026",
  "signatory_name": "Dr. Sarah Connor",
  "signatory_title": "Lead Instructor",
  "recipients": [
    {
      "name": "Alice Johnson",
      "email": "alice@example.com"
    },
    {
      "name": "Bob Smith",
      "email": "bob@example.com"
    }
  ]
}
```

**Response (`202 Accepted`):**
```json
{
  "job_id": "b73d6b05-021c-42b7-a3e9-74d6f6e804f9",
  "message": "Certificate generation job accepted and processing in background.",
  "status": "PENDING",
  "total_recipients": 2,
  "status_url": "http://127.0.0.1:8000/api/v1/jobs/b73d6b05-021c-42b7-a3e9-74d6f6e804f9"
}
```

*(Note: If you want the API to wait until all certificates finish before responding, you can add `?sync=true` to the URL).*

---

### 2. Check the Status & Progress of a Job

**Endpoint:** `GET /api/v1/jobs/{job_id}`

Replace `{job_id}` with the ID returned from the first step:
```bash
curl http://127.0.0.1:8000/api/v1/jobs/b73d6b05-021c-42b7-a3e9-74d6f6e804f9
```

**Response shows:**
- Overall job status (`PENDING`, `PROCESSING`, `COMPLETED`, `PARTIALLY_COMPLETED`)
- Total, processed, success, and failed counts
- Progress percentage (e.g. `100.0%`)
- List of each recipient with their certificate ID, status, and download URL.

---

### 3. Retrieve and Download Certificates

#### Option A: Download an Individual Certificate PDF
- **Endpoint:** `GET /api/v1/certificates/{certificate_id}/download`
- Streams the generated `.pdf` file directly to your browser or downloads it.

#### Option B: Download All Certificates as a ZIP Archive
- **Endpoint:** `GET /api/v1/jobs/{job_id}/download-all`
- Bundles all successfully generated certificates from that job into a single `.zip` file for quick downloading.

---

## 🧪 Running the Tests

To make sure everything is working properly, run:

```bash
pytest -v
```

All 24 automated tests will run and pass!

To check test coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

---

## 🧠 Simple Design Decisions Explained

Here is why certain decisions were made in this project:

1. **Why FastAPI?**  
   FastAPI is lightweight, modern, and has built-in support for background tasks. It also gives us interactive API documentation (`/docs`) automatically.

2. **Why Background Processing?**  
   Generating PDF files takes time. If a user submits 500 recipients, doing it synchronously would freeze the request and cause browser timeouts. By generating in the background, the API responds right away with `202 Accepted` and lets the client check progress at any time.

3. **Why Failure Isolation?**  
   If someone accidentally submits an invalid recipient (e.g. empty name or bad email), we shouldn't throw away the whole batch of 100 people. The system marks only the bad entry as `FAILED` (with a clear explanation like "Recipient name is required") and successfully creates certificates for everyone else.

4. **Why SQLite & SQLAlchemy?**  
   SQLite is built into Python and requires zero complicated database setup to run locally. SQLAlchemy organizes our tables (`jobs` and `certificates`) so they can easily scale to PostgreSQL in the future if needed.

5. **Why ReportLab?**  
   ReportLab draws crisp vector PDFs with borders, text, seals, and signatures directly in Python without needing external browser tools or heavyweight engines.

---

## 📂 Project Structure

```text
Bulk-Certificate-Generator/
├── app/
│   ├── main.py                     # Entry point of the FastAPI application
│   ├── config.py                   # App settings (folders, database path)
│   ├── database.py                 # SQLite database connection setup
│   ├── models.py                   # Database tables (Job and Certificate)
│   ├── schemas.py                  # Input validation models
│   ├── api/
│   │   └── routes.py               # API endpoints (create, check status, download)
│   └── services/
│       ├── certificate_generator.py # Draws the PDF certificate template
│       ├── job_processor.py        # Validates recipients & processes jobs
│       └── storage.py              # Saves files and creates zip archives
├── tests/                          # Automated tests covering all cases
├── requirements.txt                # List of Python dependencies
├── run.py                          # Simple script to run the server
└── README.md                       # This guide
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
