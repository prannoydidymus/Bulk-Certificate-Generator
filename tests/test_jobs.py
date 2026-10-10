from fastapi.testclient import TestClient


def test_create_job_sync_execution(client: TestClient):
    payload = {
        "event_name": "Docker and Kubernetes Workshop",
        "organization_name": "Cloud Native Academy",
        "recipients": [
            {"name": "Alice Cooper", "email": "alice@example.com"},
            {"name": "Bob Dylan", "email": "bob@example.com"}
        ]
    }

    # Request with ?sync=true
    response = client.post("/api/v1/jobs?sync=true", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "job_id" in data
    assert data["total_recipients"] == 2
    assert data["status"] == "COMPLETED"

    # Query the job details
    job_id = data["job_id"]
    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200

    job_data = get_res.json()
    assert job_data["id"] == job_id
    assert job_data["status"] == "COMPLETED"
    assert job_data["total_recipients"] == 2
    assert job_data["processed_count"] == 2
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 0
    assert job_data["progress_percentage"] == 100.0
    assert len(job_data["certificates"]) == 2

    # Check certificate details
    cert1 = job_data["certificates"][0]
    assert cert1["status"] == "SUCCESS"
    assert cert1["download_url"] is not None
    assert cert1["certificate_code"].startswith("CERT-")


def test_create_job_async_execution(client: TestClient):
    payload = {
        "event_name": "Machine Learning Masterclass",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    }

    # Default async request (BackgroundTasks in TestClient run synchronously at end of request)
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202

    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Verify job status
    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200
    job_data = get_res.json()
    assert job_data["id"] == job_id
    assert job_data["success_count"] == 1


def test_list_jobs(client: TestClient):
    # Create two jobs
    payload1 = {
        "event_name": "Job 1",
        "recipients": [{"name": "User 1"}]
    }
    payload2 = {
        "event_name": "Job 2",
        "recipients": [{"name": "User 2"}]
    }
    client.post("/api/v1/jobs?sync=true", json=payload1)
    client.post("/api/v1/jobs?sync=true", json=payload2)

    list_res = client.get("/api/v1/jobs")
    assert list_res.status_code == 200
    jobs_list = list_res.json()
    assert len(jobs_list) >= 2


def test_get_nonexistent_job_returns_404(client: TestClient):
    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_root_and_health_endpoints(client: TestClient):
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "Bulk Certificate Generator" in root_res.json()["service"]

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"


def test_list_jobs_with_status_filter(client: TestClient):
    payload = {
        "event_name": "Completed Event",
        "recipients": [{"name": "User Completed"}]
    }
    client.post("/api/v1/jobs?sync=true", json=payload)

    res = client.get("/api/v1/jobs?status=COMPLETED")
    assert res.status_code == 200
    jobs = res.json()
    assert all(j["status"] == "COMPLETED" for j in jobs)


def test_get_db_session_lifecycle():
    from app.database import get_db
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass


