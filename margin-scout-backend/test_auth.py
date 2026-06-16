import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

print("1. Testing /auth/register...")
register_response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "integration_test@example.com",
    "username": "integrationuser",
    "password": "SecurePassword123"
})
assert register_response.status_code == 201, f"Expected 201, got {register_response.status_code}"
register_data = register_response.json()
access_token = register_data["access_token"]
user_id = register_data["user_id"]
print(f"User registered: {user_id}")

print("\n2. Testing /auth/me (with token)...")
me_response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
assert me_response.status_code == 200, f"Expected 200, got {me_response.status_code}"
user_data = me_response.json()
print(f"User profile retrieved: {user_data['email']}")

print("\n3. Testing /auth/login...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "integration_test@example.com",
    "password": "SecurePassword123"
})
assert login_response.status_code == 200, f"Expected 200, got {login_response.status_code}"
login_data = login_response.json()
print(f"Login successful")

print("\n4. Testing /auth/refresh...")
refresh_response = requests.post(f"{BASE_URL}/auth/refresh", json={
    "refresh_token": login_data["refresh_token"]
})
assert refresh_response.status_code == 200, f"Expected 200, got {refresh_response.status_code}"
new_token = refresh_response.json()["access_token"]
print(f"Token refreshed")

print("\n5. Testing invalid token (should return 401)...")
invalid_response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": "Bearer invalid_token_here"}
)
assert invalid_response.status_code == 401, f"Expected 401, got {invalid_response.status_code}"
print(f"Invalid token rejected")

print("\nAll integration tests passed!")
