import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Config:
    # Get absolute project root path dynamically
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Adjust path based on project structure

    # Paths (Ensure they are absolute)
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_PATH = DATA_DIR / "raw"
    PROCESSED_DATA_PATH = DATA_DIR / "processed"
    MODEL_PATH = BASE_DIR / "models"
    LOGS_PATH = BASE_DIR / "logs"

    # API Configuration (Load from environment variables)
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

    # NLP Settings
    STOPWORDS_LANGUAGE = "english"

    # Model Parameters
    MODEL_NAME = "bert-base-uncased"

    @staticmethod
    def check_config():
        """Checks if API keys are set properly."""
        missing_keys = [key for key in [ "ALPHA_VANTAGE_API_KEY"]
                        if not os.getenv(key)]
        if missing_keys:
            print(f"⚠️ Warning: Missing API Keys: {', '.join(missing_keys)}")
        else:
            print("✅ All API keys are set!")

# Example usage
if __name__ == "__main__":
    print("Base Directory:", Config.BASE_DIR)
    print("Raw Data Path:", Config.RAW_DATA_PATH)
    print("Processed Data Path:", Config.PROCESSED_DATA_PATH)
    print("Model Path:", Config.MODEL_PATH)
    print("Logs Path:", Config.LOGS_PATH)
    Config.check_config()
