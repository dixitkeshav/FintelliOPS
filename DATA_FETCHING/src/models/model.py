from transformers import pipeline

# Load sentiment analysis model
sentiment_model = pipeline("sentiment-analysis")

def predict_sentiment(text):
    """Predicts sentiment of a given text."""
    return sentiment_model(text)

if __name__ == "__main__":
    sample_text = "The stock market is performing exceptionally well today."
    print(predict_sentiment(sample_text))
