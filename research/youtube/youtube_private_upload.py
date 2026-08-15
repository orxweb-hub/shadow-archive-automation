import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


VIDEO_FILE = "video/final.mp4"

CLIENT_JSON = os.environ["YOUTUBE_OAUTH_CLIENT_JSON"]
REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]

client = json.loads(CLIENT_JSON)

credentials = Credentials(
    None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client["web"]["client_id"],
    client_secret=client["web"]["client_secret"],
    scopes=["https://www.googleapis.com/auth/youtube"],
)

youtube = build(
    "youtube",
    "v3",
    credentials=credentials,
)

body = {
    "snippet": {
        "title": "MV Joyita: The Ship That Vanished Without a Trace",
        "description": """The MV Joyita disappeared in 1955 under mysterious circumstances.

This video explores the known facts surrounding the disappearance, the official investigation, and the unanswered questions that remain.

Shadow Archive
Mystery • Unsolved Cases • Real Events
""",
        "tags": [
            "MV Joyita",
            "Joyita mystery",
            "unsolved mystery",
            "missing ship",
            "real mystery",
            "Shadow Archive",
        ],
        "categoryId": "24",
    },
    "status": {
        "privacyStatus": "private",
        "selfDeclaredMadeForKids": False,
    },
}

media = MediaFileUpload(
    VIDEO_FILE,
    chunksize=8 * 1024 * 1024,
    resumable=True,
)

print("==========================================")
print("STARTING YOUTUBE PRIVATE UPLOAD")
print("==========================================")

request = youtube.videos().insert(
    part="snippet,status",
    body=body,
    media_body=media,
)

response = None

while response is None:
    status, response = request.next_chunk()

    if status:
        progress = int(status.progress() * 100)
        print(f"Upload progress: {progress}%")

print("==========================================")
print("YOUTUBE UPLOAD SUCCESS")
print("Video ID:", response["id"])
print("Privacy: PRIVATE")
print("==========================================")
