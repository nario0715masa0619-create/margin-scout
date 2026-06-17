import httpx
import time

def test_bg_task():
    # Login to get token
    res = httpx.post("http://127.0.0.1:8000/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
    if res.status_code != 200:
        # Register
        res = httpx.post("http://127.0.0.1:8000/api/v1/auth/register", json={"email": "test@example.com", "username": "testuser", "password": "password123"})
        res = httpx.post("http://127.0.0.1:8000/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
    
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create job
    print("Creating job...")
    payload = {
        "title": "Test BG Task",
        "conditions": {
            "keywords": ["test"],
            "sources": ["mercari"],
            "days_back": 30,
            "min_sales": 1
        }
    }
    res = httpx.post("http://127.0.0.1:8000/api/v1/research-jobs/", json=payload, headers=headers)
    job = res.json()
    job_id = job["id"]
    print(f"Created job: {job_id}, status: {job['status']}")

    # Poll status
    for i in range(10):
        time.sleep(1)
        res = httpx.get(f"http://127.0.0.1:8000/api/v1/research-jobs/{job_id}", headers=headers)
        status = res.json()["status"]
        print(f"Poll {i}: status is {status}")
        if status in ["completed", "failed"]:
            break

if __name__ == "__main__":
    test_bg_task()
