import pytest

def test_user_a_cannot_see_user_b_jobs(client, auth_headers_a, auth_headers_b):
    client.post("/api/v1/research-jobs/", json={"title": "Job B", "conditions": {}}, headers=auth_headers_b)
    
    res = client.get("/api/v1/research-jobs/", headers=auth_headers_a)
    assert res.status_code == 200
    assert len(res.json()) == 0

def test_user_a_cannot_access_user_b_job_by_id(client, auth_headers_a, auth_headers_b):
    create_res = client.post("/api/v1/research-jobs/", json={"conditions": {}}, headers=auth_headers_b)
    job_id_b = create_res.json()["id"]
    
    res = client.get(f"/api/v1/research-jobs/{job_id_b}", headers=auth_headers_a)
    assert res.status_code == 404 

def test_user_a_cannot_delete_user_b_job(client, auth_headers_a, auth_headers_b):
    create_res = client.post("/api/v1/research-jobs/", json={"conditions": {}}, headers=auth_headers_b)
    job_id_b = create_res.json()["id"]
    
    res = client.delete(f"/api/v1/research-jobs/{job_id_b}", headers=auth_headers_a)
    assert res.status_code == 404 
