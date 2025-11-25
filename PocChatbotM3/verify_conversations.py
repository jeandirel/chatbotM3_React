import requests
import json

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Login failed:", response.text)
        return None

def test_conversations():
    token = get_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Conversation
    print("Creating conversation...")
    response = requests.post(
        f"{BASE_URL}/api/conversations",
        headers=headers,
        json={"title": "Test Conversation"}
    )
    if response.status_code == 200:
        conv = response.json()
        print(f"Created: {conv['id']} - {conv['title']}")
        conv_id = conv['id']
    else:
        print("Failed to create conversation:", response.text)
        return

    # 2. List Conversations
    print("\nListing conversations...")
    response = requests.get(f"{BASE_URL}/api/conversations", headers=headers)
    if response.status_code == 200:
        convs = response.json()
        print(f"Found {len(convs)} conversations")
        found = any(c['id'] == conv_id for c in convs)
        print(f"New conversation found in list: {found}")
    else:
        print("Failed to list conversations:", response.text)

    # 3. Send Message to Conversation
    print("\nSending message...")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json={
            "message": "Hello in conversation",
            "conversation_id": conv_id
        }
    )
    if response.status_code == 200:
        print("Message sent successfully")
        print("Response:", response.json()['response'])
    else:
        print("Failed to send message:", response.text)

    # 4. Get Messages
    print("\nGetting messages...")
    response = requests.get(f"{BASE_URL}/api/conversations/{conv_id}/messages", headers=headers)
    if response.status_code == 200:
        msgs = response.json()
        print(f"Found {len(msgs)} messages")
    else:
        print("Failed to get messages:", response.text)

    # 5. Delete Conversation
    print("\nDeleting conversation...")
    response = requests.delete(f"{BASE_URL}/api/conversations/{conv_id}", headers=headers)
    if response.status_code == 200:
        print("Deleted successfully")
    else:
        print("Failed to delete:", response.text)

if __name__ == "__main__":
    test_conversations()
