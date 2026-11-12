import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY is missing from .env")

response = requests.get(
    "https://openrouter.ai/api/v1/key",
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=20,
)

response.raise_for_status()
data = response.json()["data"]

print("Total usage:", data.get("usage"))
print("Today's usage:", data.get("usage_daily"))
print("This week's usage:", data.get("usage_weekly"))
print("This month's usage:", data.get("usage_monthly"))
print("Key limit:", data.get("limit"))
print("Remaining key limit:", data.get("limit_remaining"))
print("Free-model daily requests:", data.get("free_model_daily_requests"))