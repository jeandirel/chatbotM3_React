import requests
import sys

try:
    response = requests.post(
        "http://localhost:8000/token",
        data={"username": "admin", "password": "admin123"},
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("LOGIN SUCCESS")
    else:
        print("LOGIN FAILED")
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
