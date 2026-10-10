import io
import zipfile
from fastapi.testclient import TestClient


def test_retrieve_and_download_certificate(client: TestClient):
    payload = {
        "event_name": "Cloud Architecture Summit",
        "recipients": [
            {"name": "Ada Lovelace", "email": "ada@computing.org"}
        ]
    }
    create_res = client.post("/api/v1/jobs?sync=true", json=payload)
    job_id = create_res.json()["job_id"]

    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = job_data["certificates"][0]["id"]

    # 1. Retrieve metadata
    meta_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["id"] == cert_id
    assert meta_data["recipient_name"] == "Ada Lovelace"
    assert meta_data["status"] == "SUCCESS"
    assert meta_data["download_url"] is not None

    # 2. Download the certificate PDF
    dl_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert "attachment" in dl_res.headers.get("content-disposition", "")
    assert dl_res.content.startswith(b"%PDF-")


def test_download_failed_certificate_returns_400(client: TestClient):
    payload = {
        "event_name": "Security Workshop",
        "recipients": [
            {"name": "", "email": "fail@test.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs?sync=true", json=payload)
    job_id = create_res.json()["job_id"]

    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = job_data["certificates"][0]["id"]

    dl_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_res.status_code == 400
    assert "cannot be downloaded" in dl_res.json()["detail"]


def test_download_nonexistent_certificate_returns_404(client: TestClient):
    dl_res = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download")
    assert dl_res.status_code == 404


def test_download_all_certificates_as_zip(client: TestClient):
    payload = {
        "event_name": "DevOps Bootcamp",
        "recipients": [
            {"name": "DevOps Ninja", "email": "ninja@devops.com"},
            {"name": "Site Reliability Expert", "email": "sre@devops.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs?sync=true", json=payload)
    job_id = create_res.json()["job_id"]

    zip_res = client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
    assert "attachment" in zip_res.headers.get("content-disposition", "")

    # Inspect zip contents
    zip_buffer = io.BytesIO(zip_res.content)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        for name in namelist:
            assert name.endswith(".pdf")


def test_get_nonexistent_certificate_metadata_returns_404(client: TestClient):
    res = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_download_all_for_nonexistent_job_returns_404(client: TestClient):
    res = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000/download-all")
    assert res.status_code == 404


def test_download_all_when_no_successful_certs(client: TestClient):
    payload = {
        "event_name": "No Success Event",
        "recipients": [{"name": ""}]
    }
    create_res = client.post("/api/v1/jobs?sync=true", json=payload)
    job_id = create_res.json()["job_id"]

    res = client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert res.status_code == 404
    assert "no successfully generated" in res.json()["detail"].lower()


def test_download_file_missing_on_disk_returns_404(client: TestClient, db_session):
    import os
    payload = {
        "event_name": "File Removed Event",
        "recipients": [{"name": "Ghost User"}]
    }
    create_res = client.post("/api/v1/jobs?sync=true", json=payload)
    job_id = create_res.json()["job_id"]
    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = job_data["certificates"][0]["id"]

    from app.models import Certificate
    cert_obj = db_session.query(Certificate).filter(Certificate.id == cert_id).first()
    if cert_obj and cert_obj.file_path and os.path.exists(cert_obj.file_path):
        os.remove(cert_obj.file_path)

    res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert res.status_code == 404
    assert "does not exist on disk" in res.json()["detail"].lower()

