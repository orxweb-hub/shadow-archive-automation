import json
import os
from datetime import datetime, timedelta, timezone

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

# ==========================================
# TEST YAYIN ZAMANI
# ==========================================
# Şimdilik videoyu 10 dakika sonrasına planlıyoruz.
# Sistem başarıyla çalıştıktan sonra bunu Telegram'dan
# gelen gerçek yayın saatine bağlayacağız.

publish_time = datetime.now(timezone.utc) + timedelta(minutes=10)

publish_at = publish_time.strftime("%Y-%m-%dT%H:%M:%SZ")

# ==========================================
# VIDEO BILGILERI
# ==========================================

title = "MV Joyita: 25 Kişi Nasıl Ortadan Kayboldu?"

description = """MV Joyita, 1955 yılında Pasifik Okyanusu'nda kaybolduktan
sonra terk edilmiş ve suyla dolmuş halde bulunan gizemli bir gemiydi.

Bu videoda MV Joyita olayının kronolojisini, gemide bulunan izleri,
resmî soruşturmayı ve bugün hâlâ cevaplanmamış soruları inceliyoruz.

Shadow Archive
Mystery • Unsolved Cases • Real Events

Kaynaklar:
National Library of New Zealand
Official MV Joyita Inquiry Records

#MVJoyita #Gizem #ÇözülemeyenOlaylar #GerçekOlaylar
#GizemliOlaylar #ShadowArchive
"""

tags = [
    "MV Joyita",
    "MV Joyita mystery",
    "Joyita mystery",
    "unsolved mystery",
    "unsolved cases",
    "missing ship",
    "mystery",
    "real mystery",
    "true mystery",
    "Shadow Archive",
]

body = {
    "snippet": {
        "title": title,
        "description": description,
        "tags": tags,
        "categoryId": "24",
    },
    "status": {
        "privacyStatus": "private",
        "publishAt": publish_at,
        "selfDeclaredMadeForKids": False,
    },
}

media = MediaFileUpload(
    VIDEO_FILE,
    chunksize=8 * 1024 * 1024,
    resumable=True,
)

print("==========================================")
print("SHADOW ARCHIVE YOUTUBE SCHEDULED UPLOAD")
print("==========================================")
print("Title:", title)
print("Scheduled UTC:", publish_at)
print("Privacy: PRIVATE")
print("Upload starting...")
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
print("==========================================")
print("Video ID:", response["id"])
print("Title:", response["snippet"]["title"])
print("Scheduled:", response["status"].get("publishAt"))
print("Privacy:", response["status"]["privacyStatus"])
print("==========================================")
