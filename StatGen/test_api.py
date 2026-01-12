"""
Debug script to test Groq API connection.
"""
import requests
import json
import os

API_KEY = os.environ.get("GROQ_API_KEY", "")
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "user", "content": "Say hello in one word."}
    ],
    "max_tokens": 10,
}

print("Testing Groq API...")
print(f"URL: {BASE_URL}")
print(f"Model: {payload['model']}")
print()

try:
    response = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("SUCCESS!")
        print(f"Response: {data['choices'][0]['message']['content']}")
    else:
        print("ERROR!")
        print(f"Response Body: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
