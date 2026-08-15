import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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

youtube = build("youtube", "v3", credentials=credentials)

response = youtube.channels().list(
    part="snippet",
    mine=True
).execute()

for channel in response.get("items", []):
    print("================================")
    print("YOUTUBE CONNECTION SUCCESS")
    print("Channel:", channel["snippet"]["title"])
    print("================================")
