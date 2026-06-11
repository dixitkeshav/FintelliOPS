import re
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('stopwords')
nltk.download('punkt')

def clean_text(text):
    """Cleans raw text by removing HTML, special characters, and stopwords."""
    text = BeautifulSoup(text, "html.parser").get_text()  # Remove HTML tags
    text = re.sub(r"[^a-zA-Z]", " ", text)  # Keep only letters
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    return " ".join(tokens)

if __name__ == "__main__":
    sample_text = "<html>Breaking News: Market crashes due to economic downturn!</html>"
    print(clean_text(sample_text))
