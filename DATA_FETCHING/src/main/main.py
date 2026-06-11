#FETCH LIVE FINANCIAL NEWS AND CLEAN IT

import pandas as pd
import numpy as np
import nltk
import re
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import requests

# Download stopwords
nltk.download('stopwords')
nltk.download('punkt')

# Function to clean text
def clean_text(text):
    text = BeautifulSoup(text, "html.parser").get_text()  # Remove HTML tags
    text = re.sub(r"[^a-zA-Z]", " ", text)  # Remove special characters
    text = text.lower()  # Convert to lowercase
    tokens = word_tokenize(text)  # Tokenize words
    tokens = [word for word in tokens if word not in stopwords.words('english')]  # Remove stopwords
    return " ".join(tokens)

# Example: Fetch a financial news article
def fetch_financial_news():
    url = f"https://www.alphavantage.co/query"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

if __name__ == "__main__":
    print("Fetching financial news...")
    raw_news = fetch_financial_news()
    if raw_news:
        cleaned_news = clean_text(raw_news)
        print("Cleaned Text:", cleaned_news[:500])  # Print first 500 characters
    else:
        print("Failed to fetch news.")
