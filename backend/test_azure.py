"""Quick smoke test for Azure OpenAI credentials."""
import os
from pathlib import Path

from dotenv import load_dotenv
import openai

# Load .env next to this script (works whether you run from backend/ or repo root)
load_dotenv(Path(__file__).resolve().parent / ".env")

azure_endpoint = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
if azure_endpoint.endswith("/openai/v1"):
    azure_endpoint = azure_endpoint[: -len("/openai/v1")]

api_key = os.getenv("AZURE_OPENAI_API_KEY")
model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4.1-mini")

if not azure_endpoint or not api_key:
    raise SystemExit(
        "Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY in backend/.env"
    )

client = openai.AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=api_key,
    api_version="2024-08-01-preview",
)

response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Say: Azure connected successfully"}],
    max_tokens=50,
)
print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
