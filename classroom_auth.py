import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses",
    "https://www.googleapis.com/auth/classroom.rosters",
    "https://www.googleapis.com/auth/classroom.announcements",
    "https://www.googleapis.com/auth/classroom.coursework.students"
]

CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "config/webportal_credentials.json")
TOKEN_FILE = os.environ.get("CLASSROOM_TOKEN_FILE", "config/classroom_token.pickle")

def get_classroom_service():
    """Authenticate and return a Classroom API service instance."""
    creds = None

    # 🔄 Load and refresh token if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print("⚠️ Token refresh failed:", e)
            creds = None

    # 🆕 Trigger login if no valid creds
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES
        )
        creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent")

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("classroom", "v1", credentials=creds)
