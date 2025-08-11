import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURATION ---
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "config/webportal_credentials.json")
TOKEN_FILE = os.environ.get("YOUTUBE_TOKEN_FILE", "config/token.pickle")

# --- AUTHENTICATION ---
def get_authenticated_service():
    """Authenticate and return a YouTube API service instance."""
    credentials = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)

    if not credentials:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)

    return build("youtube", "v3", credentials=credentials)

# --- PLAYLIST HANDLING ---
def create_playlist_if_missing(youtube, class_name):
    """
    Ensure a playlist exists for the given class name.
    If it doesn't exist, create a new unlisted one.
    """
    existing = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    ).execute()

    for item in existing.get("items", []):
        if item["snippet"]["title"] == class_name:
            return item["id"]

    playlist = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": class_name,
                "description": f"Playlist for {class_name}"
            },
            "status": {
                "privacyStatus": "unlisted"
            }
        }
    ).execute()

    return playlist["id"]

# --- VIDEO UPLOAD ---
def upload_video_to_youtube(file_path, title, description, playlist_id=None, tags=None):
    """
    Upload a video to YouTube with the given metadata.
    Optionally add to a playlist.
    """
    youtube = get_authenticated_service()
    media = MediaFileUpload(file_path)

    video_response = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "27",  # Education
                "tags": tags or []
            },
            "status": {
                "privacyStatus": "unlisted",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=media
    ).execute()

    video_id = video_response.get("id")
    print(f"✅ Uploaded: {title} (Video ID: {video_id})")

    if playlist_id:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        print(f"📁 Added to Playlist: {playlist_id}")
        

    return video_id
