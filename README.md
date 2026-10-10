# Bulk Certificate Generator API 📜🚀

A production-ready, high-performance Backend REST API built with **FastAPI**, **SQLAlchemy (SQLite)**, and **ReportLab** that accepts bulk certificate generation requests, processes them efficiently with asynchronous background workers, isolates errors per recipient, tracks job lifecycle progress, and serves generated PDF certificates individually or as bundled ZIP archives.

---

## 🌟 Key Features

- **Bulk Certificate Generation**: Submit tens, hundreds, or thousands of recipients in a single API call.
- **Asynchronous Background Processing**: API immediately responds with `202 Accepted` and a job tracking URL while certificates generate in the background without blocking HTTP requests. (Synchronous mode `?sync=true` also supported).
- **Fault-Tolerant & Failure Isolation**: An invalid recipient (e.g., missing name or malformed email) or rendering issue fails that single certificate with an explanatory error reason without halting or corrupting the rest of the batch.
- **Detailed Progress Tracking**: Monitor real-time job status (`PENDING`, `PROCESSING`, `COMPLETED`, `PARTIALLY_COMPLETED`, `FAILED`), recipient metrics, and completion percentage.
- **Predefined Vector PDF Template**: High-quality landscape A4 certificate with elegant navy/gold double borders, corner ornaments, recipient distinction notes, official verification seals, and custom signatory titles generated using ReportLab.
- **Flexible Retrieval**: Download individual PDF certificates by certificate ID, or download all generated certificates in a job as a compressed ZIP archive (`/download-all`).
- **Interactive Documentation**: Built-in Swagger UI (`/docs`) and ReDoc (`/redoc`).
- **99% Automated Test Coverage**: Comprehensive test suite covering every core feature, edge case, validation failure, and retrieval path.

---

## 🏗️ Architecture & Design Decisions

### 1. Framework Choice: FastAPI vs. Django / Flask
- **Why FastAPI**: 
  - Native asynchronous support and built-in `BackgroundTasks` enable instant, non-blocking HTTP responses for heavy PDF generation jobs.
  - Automatic request validation and schema serialisation using Pydantic v2.
  - Auto-generated interactive OpenAPI/Swagger documentation (`/docs`).
  - High throughput and minimal overhead compared to full-stack frameworks like Django.

### 2. Database: Relational Database (SQLite + SQLAlchemy 2.0)
- **Why SQLite with SQLAlchemy**:
  - Requires zero external infrastructure (like PostgreSQL or MySQL servers) to run locally or in tests while maintaining full relational integrity, foreign key cascades, and ACID compliance.
  - SQLAlchemy ORM abstracts the schema, allowing seamless switching to PostgreSQL in production simply by setting the `DATABASE_URL` environment variable.
  - Schema models:
    - **`Job`**: Tracks the overall batch (event name, issuer, status, counts, timestamps).
    - **`Certificate`**: Represents individual recipient certificates linked to `Job` with foreign key, status, file paths, and individual error diagnostics.

### 3. Bulk Processing: Background Worker vs. Synchronous
- Generating PDFs involves I/O and vector drawing operations. Generating hundreds of certificates synchronously would cause HTTP timeouts on client browsers and API gateways.
- By default, `POST /api/v1/jobs` registers a background worker task and immediately returns `202 Accepted` with the `job_id` and tracking status URL.
- Clients can poll `GET /api/v1/jobs/{job_id}` to check real-time progress.
- An optional `?sync=true` query parameter is provided for automated testing or small scripts that prefer waiting for the completed response.

### 4. Failure Isolation Strategy
- Instead of rejecting an entire bulk request when one recipient has invalid data (or failing the entire batch mid-way), the processor performs item-level validation and error trapping.
- Valid recipients produce certificates (`status: SUCCESS`).
- Invalid or problematic recipients are recorded with `status: FAILED` and an explicit diagnostic message (`error_message: "Validation Error: ..."`).
- The parent job status automatically reflects the aggregate result:
  - `COMPLETED`: All recipients succeeded.
  - `PARTIALLY_COMPLETED`: Some recipients succeeded while others failed.
  - `FAILED`: All recipients failed.

---

## 📁 Project Structure

```text
Bulk-Certificate-Generator/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup, CORS, lifespan
│   ├── config.py                   # Configuration and environment settings
│   ├── database.py                 # SQLAlchemy engine, session maker, get_db dependency
│   ├── models.py                   # Relational DB models (Job, Certificate)
│   ├── schemas.py                  # Pydantic v2 schemas for requests & responses
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py               # REST API endpoints
│   └── services/
│       ├── __init__.py
│       ├── certificate_generator.py # Predefined ReportLab PDF template generator
│       ├── job_processor.py        # Batch execution engine & failure isolation logic
│       └── storage.py              # File storage & ZIP archive bundling
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures (isolated DB & client)
│   ├── test_jobs.py                # Job lifecycle, async/sync processing tests
│   ├── test_generator.py           # Unit tests for ReportLab PDF rendering
│   ├── test_validation.py          # Input validation tests (empty fields, 422 errors)
│   ├── test_failure_handling.py    # Failure isolation & partial success tests
│   └── test_retrieval.py           # Certificate & ZIP download tests
├── requirements.txt                # Pinned production and testing dependencies
├── run.py                          # Application entry point script
├── .gitignore                      # Git ignore rules
└── README.md                       # Complete documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python **3.10+** (Tested and compatible with Python 3.10, 3.11, 3.12, 3.13, 3.14)
- `pip` package manager

### 1. Clone the Repository
```bash
git clone https://github.com/prannoydidymus/Bulk-Certificate-Generator.git
cd Bulk-Certificate-Generator
```

### 2. Create and Activate a Virtual Environment
- **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **On Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Start the development server with Uvicorn:
```bash
python run.py
```
Or directly via Uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once started:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc UI**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/health`

---

## 🧪 Running Tests

The test suite runs with `pytest` and verifies input validation, certificate PDF rendering, asynchronous status tracking, individual failure isolation, and certificate retrieval:

```bash
pytest -v
```

To run with test coverage reporting:
```bash
pytest --cov=app --cov-report=term-missing
```

*(Current test suite passes **24/24 tests** with **99% total coverage**).*

---

## 📡 API Reference & Usage Guide

### 1. Submit a Certificate Generation Request

- **Endpoint**: `POST /api/v1/jobs`
- **Query Parameter (Optional)**: `?sync=true` (Runs synchronously and returns 201; default is false which returns 202 and runs in background).
- **Request Body**:
  ```json
  {
    "event_name": "Full Stack Web Development Masterclass",
    "organization_name": "Tech Academy International",
    "issue_date": "October 10, 2026",
    "signatory_name": "Dr. Sarah Connor",
    "signatory_title": "Head of Certification",
    "recipients": [
      {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "custom_note": "Graduated with Honors"
      },
      {
        "name": "Bob Smith",
        "email": "bob@example.com"
      },
      {
        "name": "",
        "email": "invalid_user@example.com"
      }
    ]
  }
  ```

- **Example `curl` Request**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
       -H "Content-Type: application/json" \
       -d '{
         "event_name": "Full Stack Web Development Masterclass",
         "organization_name": "Tech Academy International",
         "recipients": [
           {"name": "Alice Johnson", "email": "alice@example.com"},
           {"name": "Bob Smith", "email": "bob@example.com"}
         ]
       }'
  ```

- **Response (`202 Accepted`)**:
  ```json
  {
    "job_id": "b73d6b05-021c-42b7-a3e9-74d6f6e804f9",
    "message": "Certificate generation job accepted and processing in background.",
    "status": "PENDING",
    "total_recipients": 2,
    "status_url": "http://127.0.0.1:8000/api/v1/jobs/b73d6b05-021c-42b7-a3e9-74d6f6e804f9"
  }
  ```

---

### 2. Check Job Progress & Results

- **Endpoint**: `GET /api/v1/jobs/{job_id}`
- **Example `curl` Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/jobs/b73d6b05-021c-42b7-a3e9-74d6f6e804f9"
  ```

- **Response (`200 OK`)**:
  ```json
  {
    "id": "b73d6b05-021c-42b7-a3e9-74d6f6e804f9",
    "event_name": "Full Stack Web Development Masterclass",
    "organization_name": "Tech Academy International",
    "issue_date": "October 10, 2026",
    "signatory_name": "Dr. Sarah Connor",
    "signatory_title": "Head of Certification",
    "status": "PARTIALLY_COMPLETED",
    "total_recipients": 3,
    "processed_count": 3,
    "success_count": 2,
    "failed_count": 1,
    "progress_percentage": 100.0,
    "created_at": "2026-10-10T12:50:00Z",
    "completed_at": "2026-10-10T12:50:01Z",
    "certificates": [
      {
        "id": "e93ab7e2-78d1-443f-b648-912fbbd279cf",
        "job_id": "b73d6b05-021c-42b7-a3e9-74d6f6e804f9",
        "recipient_name": "Alice Johnson",
        "recipient_email": "alice@example.com",
        "certificate_code": "CERT-B73D6B05-E93AB7",
        "status": "SUCCESS",
        "file_size": 2420,
        "error_message": null,
        "download_url": "http://127.0.0.1:8000/api/v1/certificates/e93ab7e2-78d1-443f-b648-912fbbd279cf/download",
        "created_at": "2026-10-10T12:50:00Z"
      },
      {
        "id": "f10cd832-10f8-48b4-8cf1-97b5d2036c0a",
        "job_id": "b73d6b05-021c-42b7-a3e9-74d6f6e804f9",
        "recipient_name": "",
        "recipient_email": "invalid_user@example.com",
        "certificate_code": "CERT-B73D6B05-F10CD8",
        "status": "FAILED",
        "file_size": null,
        "error_message": "Validation Error: Recipient name is required and cannot be blank.",
        "download_url": null,
        "created_at": "2026-10-10T12:50:00Z"
      }
    ]
  }
  ```

---

### 3. Retrieve & Download Generated Certificates

#### Download an Individual Certificate PDF:
- **Endpoint**: `GET /api/v1/certificates/{certificate_id}/download`
- **Example `curl` Request**:
  ```bash
  curl -O -J "http://127.0.0.1:8000/api/v1/certificates/e93ab7e2-78d1-443f-b648-912fbbd279cf/download"
  ```
- Returns the PDF binary with headers:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="Certificate_Alice_Johnson_CERT-B73D6B05-E93AB7.pdf"`

#### Download All Job Certificates as a ZIP Archive:
- **Endpoint**: `GET /api/v1/jobs/{job_id}/download-all`
- **Example `curl` Request**:
  ```bash
  curl -O -J "http://127.0.0.1:8000/api/v1/jobs/b73d6b05-021c-42b7-a3e9-74d6f6e804f9/download-all"
  ```
- Returns a ZIP archive containing all successfully generated certificates for that job.

---

### 4. List All Jobs

- **Endpoint**: `GET /api/v1/jobs?status=COMPLETED&skip=0&limit=20`
- **Example `curl` Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/jobs"
  ```

---

## 🔒 Security & Quality Standards

- **Input Sanitization**: File names for downloads are safely sanitized to prevent path traversal.
- **Thread Safety**: SQLite is configured with non-blocking threading modes (`check_same_thread=False`).
- **Resource Cleanup**: In-memory ZIP streaming avoids leftover temporary files.
- **Graceful Error Responses**: Clear HTTP error codes (400, 404, 422) with descriptive JSON messages.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
