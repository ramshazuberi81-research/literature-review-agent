import os
import requests

api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(url, headers=headers)
data = response.json()

for model in data.get("data", []):
    print(model["id"])