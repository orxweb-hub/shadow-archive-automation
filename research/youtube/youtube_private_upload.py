import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


TOPIC_FILE = Path("production_package/research/current_topic.json")
MAIN_VIDEO = Path("production_package/main/main_video.mp4")
SHORT_1 = Path("production_package/shorts/short_1.mp4")
SHORT_2 = Path("production_package/shorts/short_2.mp4")

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

TURKEY = ZoneInfo("Europe/Istanbul")


def load_topic():
    if not TOPIC_FILE.exists():
        raise FileNotFoundError(
            f"current_topic.json bulunamadı: {TOPIC_FILE}"
        )

    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "topic": data.get("topic", "Shadow Archive"),
        "title": data.get(
            "title",
            data.get("topic", "Shadow Archive")
        ),
        "description": data.get("description", ""),
        "hashtags": data.get("hashtags", []),
    }


def get_publish_day():
    """
    Yayın planı:

    09:00 → Short #1
    12:00 → Ana Video
    21:00 → Short #2

    Onay 09:00'dan önce gelirse:
        içerikler aynı gün yayınlanır.

    Onay 09:00 veya sonrasında gelirse:
        tüm içerikler ertesi güne alınır.

    Böylece hiçbir video geçmiş bir saate
    planlanmaya çalışılmaz.
    """

    now = datetime.now(TURKEY)

    today_09 = now.replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0,
    )

    if now < today_09:
        return now.date()

    return (now + timedelta(days=1)).date()


def turkey_to_utc(date_value, hour, minute):
    turkey_time = datetime(
        date_value.year,
        date_value.month,
        date_value.day,
        hour,
        minute,
        tzinfo=TURKEY,
    )

    utc_time = turkey_time.astimezone(timezone.utc)

    return utc_time.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def load_metadata():
    metadata_file = Path(
        "production_package/metadata/production.json"
    )

    if not metadata_file.exists():
        raise FileNotFoundError(
            f"production
