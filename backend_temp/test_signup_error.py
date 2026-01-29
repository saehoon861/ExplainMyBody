import requests
import json

url = "http://localhost:5000/api/signup"
data = {
    "email": "test_debug@example.com",
    "password": "password123",
    "gender": "male",
    "age": 30,
    "height": 180.0,
    "startWeight": 80.0,
    "targetWeight": 75.0,
    "goalType": "감량",
    "activityLevel": "보통",
    "goal": "건강 관리",
    "preferredExercises": ["러닝"],
    "medicalConditions": ["없음"],
    "medicalConditionsDetail": "",
    "inbodyData": {"weight": 80.0}
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
