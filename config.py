CLASSROOM_OWNER_EMAIL = "pobakara@gmail.com"  # ← Replace with real default

import os
from dotenv import load_dotenv

# Load environment variables from .env file (only in local dev)
load_dotenv()

class Config:
    # Flask security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # Debug mode (True in local dev, False in production)
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///SciMindMain.db")

    # Google API credentials
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # for YouTube Data API
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")

    # OAuth redirect URIs
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/oauth2callback")

    # YouTube specific
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    # Google Classroom specific
    GOOGLE_CLASSROOM_SCOPES = os.getenv(
        "GOOGLE_CLASSROOM_SCOPES",
        "https://www.googleapis.com/auth/classroom.courses "
        "https://www.googleapis.com/auth/classroom.rosters "
        "https://www.googleapis.com/auth/classroom.coursework.students"
    )

    # Optional: Render environment indicator
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

