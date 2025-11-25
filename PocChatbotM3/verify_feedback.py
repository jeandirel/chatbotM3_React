import requests
import sys

# 1. Login to get token
try:
    auth_response = requests.post(
        "http://localhost:8000/token",
        data={"username": "admin", "password": "admin123"},
    )
    if auth_response.status_code != 200:
        print("Login failed")
        sys.exit(1)
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Interactions
    print("Fetching interactions...")
    interactions_response = requests.get("http://localhost:8000/api/interactions", headers=headers)
    print(f"Interactions Status: {interactions_response.status_code}")
    if interactions_response.status_code == 200:
        print(f"Interactions Count: {len(interactions_response.json())}")
    else:
        print(f"Error: {interactions_response.text}")

except Exception as e:
    print(f"Error: {e}")
