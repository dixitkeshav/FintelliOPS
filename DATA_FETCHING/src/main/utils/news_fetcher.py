import requests
import json
import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(__file__)
main_dir = os.path.abspath(os.path.join(current_dir, ".."))         # Goes to `main`
sys.path.append(main_dir)

from config.config import Config
# Class remains the same...

class NewsFetcher:
    """Class to fetch financial news from Alpha Vantage & FMP APIs."""

    @staticmethod
    def get_alpha_vantage_news(symbol="AAPL"):
        """Fetch latest news from Alpha Vantage."""
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": Config.ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return data.get("feed", [])  # Extract news feed
        else:
            print("❌ Alpha Vantage API error:", response.text)
            return []

'''    @staticmethod
    def get_fmp_news(symbol="AAPL"):
        """Fetch latest news from Financial Modeling Prep (FMP)."""
        url = f"https://financialmodelingprep.com/api/v3/stock_news"
        params = {
            "apikey": Config.FMP_API_KEY,
            "tickers": symbol,
            "limit": 10  # Fetch last 10 news articles
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()  # List of news articles
        else:
            print("❌ FMP API error:", response.text)
            return []
'''

if __name__ == "__main__":
    print("Fetching news from Alpha Vantage...")
    alpha_news = NewsFetcher.get_alpha_vantage_news()
    print(json.dumps(alpha_news, indent=4))

'''   print("\nFetching news from FMP...")
    fmp_news = NewsFetcher.get_fmp_news()
    print(json.dumps(fmp_news, indent=4))'''
