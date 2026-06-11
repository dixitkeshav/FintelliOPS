import os
import django
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from fetch_news.models import NewsArticle
from fetch_news import newsapi_client as na
from fetch_news.sentiment import analyze_financial_sentiment

# ✅ Load environment variables
load_dotenv()
API_KEY = os.getenv("NEWSAPI_KEY")

class Command(BaseCommand):
    help = "Fetches financial news from NewsAPI and stores them in the database"

    def handle(self, *args, **kwargs):
        if not API_KEY:
            self.stdout.write(self.style.ERROR("Error: NEWSAPI_KEY not found in .env"))
            return

        try:
            news_data = na.fetch_market_news(limit=30)
            if not news_data:
                self.stdout.write(self.style.WARNING("No news articles found."))
                return

            for item in news_data:
                title = item.get("title", "No Title")
                summary = item.get("summary", "No Summary")
                sentiment = "neutral"
                try:
                    s, _ = analyze_financial_sentiment(f"{title} {summary}"[:1500])
                    sentiment = (s or "neutral").lower()
                except Exception:
                    pass
                NewsArticle.objects.create(
                    title=title,
                    content=f"[{sentiment}] {summary}"[:20000],
                )

            self.stdout.write(self.style.SUCCESS(f"✅ {len(news_data)} news articles saved successfully!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error fetching news: {e}"))
