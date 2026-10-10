from fastapi.testclient import TestClient


def test_validation_rejects_missing_event_name(client: TestClient):
    payload = {
        "recipients": [{"name": "Alice"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_validation_rejects_blank_event_name(client: TestClient):
    payload = {
        "event_name": "   ",
        "recipients": [{"name": "Alice"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_rejects_empty_recipients_list(client: TestClient):
    payload = {
        "event_name": "AI Workshop",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_rejects_missing_recipients_field(client: TestClient):
    payload = {
        "event_name": "AI Workshop"
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
