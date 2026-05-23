"""Test Gemini 2.5 models."""
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# List available models first
print("Listing available models...")
try:
    for m in client.models.list():
        name = m.name
        if "gemini" in name.lower():
            print(f"  {name}")
except Exception as e:
    print(f"  Error listing: {e}")

# Try the latest ones
models_to_try = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
]

for model_name in models_to_try:
    print(f"\nTrying {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say hi",
        )
        print(f"  SUCCESS: {response.text.strip()}")
        break
    except Exception as e:
        err = str(e)
        if "429" in err:
            print(f"  Rate limited (quota: 0)")
        elif "404" in err:
            print(f"  Not found")
        else:
            print(f"  Error: {err[:200]}")
