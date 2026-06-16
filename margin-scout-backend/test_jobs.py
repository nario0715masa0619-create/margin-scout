import requests

BASE_URL = "http://localhost:8000/api/v1"

print("1. Testing unauthorized GET /research-jobs...")
resp1 = requests.get(f"{BASE_URL}/research-jobs/")
assert resp1.status_code == 401, f"Expected 401, got {resp1.status_code}"

print("2. Registering User A...")
user_a_data = {"email": "user_a@example.com", "username": "usera", "password": "SecurePassword123"}
resp_a = requests.post(f"{BASE_URL}/auth/register", json=user_a_data)
if resp_a.status_code == 400:
    resp_a = requests.post(f"{BASE_URL}/auth/login", json=user_a_data)
token_a = resp_a.json()["access_token"]
headers_a = {"Authorization": f"Bearer {token_a}"}

print("3. Registering User B...")
user_b_data = {"email": "user_b@example.com", "username": "userb", "password": "SecurePassword123"}
resp_b = requests.post(f"{BASE_URL}/auth/register", json=user_b_data)
if resp_b.status_code == 400:
    resp_b = requests.post(f"{BASE_URL}/auth/login", json=user_b_data)
token_b = resp_b.json()["access_token"]
headers_b = {"Authorization": f"Bearer {token_b}"}

print("4. User A creating job...")
job_req = {
    "title": "User A Job",
    "conditions": {"keyword": "test"}
}
resp_job_a = requests.post(f"{BASE_URL}/research-jobs/", json=job_req, headers=headers_a)
assert resp_job_a.status_code == 201, f"Expected 201, got {resp_job_a.status_code}"
job_id_a = resp_job_a.json()["id"]

print("5. User A getting jobs...")
jobs_a = requests.get(f"{BASE_URL}/research-jobs/", headers=headers_a).json()
assert any(j["id"] == job_id_a for j in jobs_a), "User A should see their job"

print("6. User B getting jobs...")
jobs_b = requests.get(f"{BASE_URL}/research-jobs/", headers=headers_b).json()
assert not any(j["id"] == job_id_a for j in jobs_b), "User B should NOT see User A's job"

print("7. User B trying to access User A's job directly...")
resp_direct = requests.get(f"{BASE_URL}/research-jobs/{job_id_a}", headers=headers_b)
assert resp_direct.status_code == 404, f"Expected 404, got {resp_direct.status_code}"

print("All multi-tenant tests passed!")
