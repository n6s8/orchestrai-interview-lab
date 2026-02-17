import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200

def test_start_interview():
    print("Testing /interview/start endpoint...")
    
    resume = """
    John Doe
    Software Engineer
    
    Skills: Python, JavaScript, React, FastAPI
    Experience: 3 years
    
    Projects:
    - Built a chat application with WebSockets
    - Created a REST API with FastAPI
    - Developed React frontend applications
    """
    
    params = {
        "candidate_name": "John Doe",
        "resume": resume
    }
    
    response = requests.post(f"{BASE_URL}/interview/start", params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}\n")
        return data.get("session_id")
    else:
        print(f"Error: {response.text}\n")
        return None

def test_get_interview(session_id):
    print(f"Testing /interview/{session_id} endpoint...")
    response = requests.get(f"{BASE_URL}/interview/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200

def test_get_messages(session_id):
    print(f"Testing /interview/{session_id}/messages endpoint...")
    response = requests.get(f"{BASE_URL}/interview/{session_id}/messages")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Messages count: {len(data['messages'])}")
        if data['messages']:
            print(f"First message: {json.dumps(data['messages'][0], indent=2)}\n")
        return True
    else:
        print(f"Error: {response.text}\n")
        return False

if __name__ == "__main__":
    print("="*50)
    print("Backend API Test Suite")
    print("="*50 + "\n")
    
    try:
        if not test_health():
            print("❌ Health check failed! Is the backend running?")
            exit(1)
        
        print("✅ Health check passed!\n")
        
        session_id = test_start_interview()
        if not session_id:
            print("❌ Failed to start interview!")
            exit(1)
        
        print("✅ Interview started!\n")
        
        import time
        print("Waiting 3 seconds for agent to process...")
        time.sleep(3)
        
        if not test_get_interview(session_id):
            print("❌ Failed to get interview status!")
            exit(1)
        
        print("✅ Got interview status!\n")
        
        if not test_get_messages(session_id):
            print("❌ Failed to get messages!")
            exit(1)
        
        print("✅ Got messages!\n")
        
        print("="*50)
        print("🎉 All tests passed!")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend!")
        print("Make sure the backend is running on http://localhost:8000")
        print("\nTo start backend:")
        print("cd backend")
        print(".\\venv\\Scripts\\Activate.ps1")
        print("python -m uvicorn src.main:app --reload")
