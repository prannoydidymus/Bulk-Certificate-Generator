from fastapi.testclient import TestClient


def test_individual_certificate_failure_isolation(client: TestClient):
    """
    Verifies that invalid recipients (missing names or malformed emails) fail gracefully
    without blocking valid recipients in the same bulk job.
    """
    payload = {
        "event_name": "Full Stack Engineering Workshop",
        "recipients": [
            {
                "name": "Sarah Connor",
                "email": "sarah@resistance.org"
            },
            {
                "name": "",  # Invalid: empty name
                "email": "empty_name@example.com"
            },
            {
                "name": "Kyle Reese",
                "email": "invalid-email-address"  # Invalid email format
            },
            {
                "name": "John Connor",
                "email": "john@resistance.org"
            }
        ]
    }

    response = client.post("/api/v1/jobs?sync=true", json=payload)
    assert response.status_code == 201

    data = response.json()
    job_id = data["job_id"]

    # Retrieve full job details
    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200

    job_data = get_res.json()
    assert job_data["total_recipients"] == 4
    assert job_data["processed_count"] == 4
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 2
    assert job_data["status"] == "PARTIALLY_COMPLETED"
    assert job_data["progress_percentage"] == 100.0

    certs = job_data["certificates"]
    assert len(certs) == 4

    # Cert 1 (Sarah) should succeed
    assert certs[0]["recipient_name"] == "Sarah Connor"
    assert certs[0]["status"] == "SUCCESS"
    assert certs[0]["download_url"] is not None

    # Cert 2 (Empty name) should fail with clear reason
    assert certs[1]["status"] == "FAILED"
    assert "name is required" in certs[1]["error_message"].lower()

    # Cert 3 (Invalid email) should fail with clear reason
    assert certs[2]["status"] == "FAILED"
    assert "invalid email format" in certs[2]["error_message"].lower()

    # Cert 4 (John) should succeed despite previous failures
    assert certs[3]["recipient_name"] == "John Connor"
    assert certs[3]["status"] == "SUCCESS"
    assert certs[3]["download_url"] is not None


def test_entire_job_failed_when_all_recipients_invalid(client: TestClient):
    payload = {
        "event_name": "Testing All Failure",
        "recipients": [
            {"name": "   ", "email": "a@example.com"},
            {"name": None, "email": "b@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs?sync=true", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    assert job_data["status"] == "FAILED"
    assert job_data["success_count"] == 0
    assert job_data["failed_count"] == 2


def test_recipient_name_too_long(client: TestClient):
    payload = {
        "event_name": "Testing Length",
        "recipients": [
            {"name": "A" * 105, "email": "toolong@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs?sync=true", json=payload)
    job_id = response.json()["job_id"]
    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    assert job_data["failed_count"] == 1
    assert "exceeds maximum allowed length" in job_data["certificates"][0]["error_message"].lower()


def test_generator_runtime_exception_isolated(client: TestClient, monkeypatch):
    from app.services.certificate_generator import CertificateTemplateGenerator

    def mock_generate_pdf(*args, **kwargs):
        raise RuntimeError("Disk write failed unexpectedly")

    monkeypatch.setattr(CertificateTemplateGenerator, "generate_pdf", mock_generate_pdf)

    payload = {
        "event_name": "Crash Test Workshop",
        "recipients": [
            {"name": "Valid Name", "email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs?sync=true", json=payload)
    job_id = response.json()["job_id"]
    job_data = client.get(f"/api/v1/jobs/{job_id}").json()

    assert job_data["status"] == "FAILED"
    assert job_data["failed_count"] == 1
    assert "Generation Error: Disk write failed unexpectedly" in job_data["certificates"][0]["error_message"]

