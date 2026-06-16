import pytest

def test_create_job(client, auth_headers_a):
    payload = {"title": "Test Job", "conditions": {"keyword": "Nintendo"}}
    res = client.post("/api/v1/research-jobs/", json=payload, headers=auth_headers_a)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Test Job"
    assert data["status"] == "pending"
    assert "id" in data

def test_get_jobs_empty(client, auth_headers_a):
    res = client.get("/api/v1/research-jobs/", headers=auth_headers_a)
    assert res.status_code == 200
    assert res.json() == []

def test_get_jobs_with_data(client, auth_headers_a):
    client.post("/api/v1/research-jobs/", json={"title": "J1", "conditions": {}}, headers=auth_headers_a)
    client.post("/api/v1/research-jobs/", json={"title": "J2", "conditions": {}}, headers=auth_headers_a)
    
    res = client.get("/api/v1/research-jobs/", headers=auth_headers_a)
    assert res.status_code == 200
    assert len(res.json()) == 2

def test_get_job_by_id(client, auth_headers_a):
    create_res = client.post("/api/v1/research-jobs/", json={"conditions": {}}, headers=auth_headers_a)
    job_id = create_res.json()["id"]
    
    res = client.get(f"/api/v1/research-jobs/{job_id}", headers=auth_headers_a)
    assert res.status_code == 200
    assert res.json()["id"] == job_id

def test_get_job_not_found(client, auth_headers_a):
    res = client.get("/api/v1/research-jobs/dummy-id", headers=auth_headers_a)
    assert res.status_code == 404

def test_delete_job(client, auth_headers_a):
    create_res = client.post("/api/v1/research-jobs/", json={"conditions": {}}, headers=auth_headers_a)
    job_id = create_res.json()["id"]
    
    res = client.delete(f"/api/v1/research-jobs/{job_id}", headers=auth_headers_a)
    assert res.status_code == 204
    
    get_res = client.get(f"/api/v1/research-jobs/{job_id}", headers=auth_headers_a)
    assert get_res.status_code == 404

def test_delete_job_not_found(client, auth_headers_a):
    res = client.delete("/api/v1/research-jobs/dummy-id", headers=auth_headers_a)
    assert res.status_code == 404
