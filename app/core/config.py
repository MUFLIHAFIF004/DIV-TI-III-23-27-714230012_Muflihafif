import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    DB_NAME: str = os.getenv("DB_NAME", "smart_meal_db")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "meal_plans")

settings = Settings()
