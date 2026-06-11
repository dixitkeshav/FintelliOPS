from dotenv import load_dotenv
import os
import requests

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def fetch_news():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "finance",
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json().get("feed", [])
    else:
        print(f"Error fetching news: {response.status_code}")
        return []
