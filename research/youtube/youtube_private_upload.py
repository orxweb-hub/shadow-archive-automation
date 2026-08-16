import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# =========================================================
# PATHS
# =========================================================

TOPIC_FILE = Path("production_package/research/current_topic.json")

MAIN_VIDEO = Path("production_package/main/main_video.mp4")

SHORT_1 = Path("production_package/shorts/short_1.mp4")
SHORT_2 = Path("production_package/shorts/short_2.mp4")


# =========================================================
# YOUTUBE AUTH
# =========================================================

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


# =========================================================
# LOAD TOPIC
# =========================================================

def load_topic():

    if not TOPIC_FILE.exists():
        raise FileNotFoundError(
            f"current_topic.json bulunamadı: {TOPIC_FILE}"
        )

    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    topic = data.get("topic", "Shadow Archive")
    title = data.get("title", topic)
    description = data.get("description", "")
    hashtags = data.get("hashtags", [])

    return {
        "topic": topic,
        "title": title,
        "description": description,
        "hashtags": hashtags,
    }


# =========================================================
# SCHEDULE
# =========================================================

TURKEY = ZoneInfo("Europe/Istanbul")


def get_next_publish_day():

    now = datetime.now(TURKEY)

    # Her onaydan sonra bir sonraki günü kullanıyoruz.
    next_day = (now + timedelta(days=1)).date()

    return next_day


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

    return utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")


# =========================================================
# TEXT
# =========================================================

def build_main_description(data):

    description = data["description"].strip()

    if not description:
        description = (
            f"{data['topic']} hakkında Shadow Archive "
            "tarafından hazırlanan araştırma videosu."
        )

    hashtags = data["hashtags"]

    if isinstance(hashtags, list):
        hashtag_text = " ".join(
            str(x) if str(x).startswith("#") else f"#{x}"
            for x in hashtags
        )
    else:
        hashtag_text = str(hashtags)

    return f"""{description}

Shadow Archive
Mystery • Unsolved Cases • Real Events

{hashtag_text}

#ShadowArchive
"""


def build_short_description(data, number):

    return f"""{data['topic']}

Shadow Archive'dan kısa bir bölüm.

Daha fazla gizemli olay ve gerçek hikâye için
Shadow Archive kanalını takip edin.

#{data['topic'].replace(" ", "")}
#ShadowArchive
#Shorts
"""


# =========================================================
# UPLOAD FUNCTION
# =========================================================

def upload_video(
    video_file,
    title,
    description,
    publish_at,
    tags,
):

    if not video_file.exists():
        raise FileNotFoundError(
            f"Video bulunamadı: {video_file}"
        )

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
        str(video_file),
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )

    print()
    print("==========================================")
    print("YOUTUBE UPLOAD")
    print("==========================================")
    print("Title:", title)
    print("File:", video_file)
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

    print()
    print("YOUTUBE UPLOAD SUCCESS")
    print("Video ID:", response["id"])
    print("Title:", response["snippet"]["title"])
    print("Scheduled:", response["status"].get("publishAt"))
    print("Privacy:", response["status"]["privacyStatus"])
    print("==========================================")

    return response


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("==========================================")
    print("SHADOW ARCHIVE — DAILY YOUTUBE PUBLISHER")
    print("==========================================")

    data = load_topic()

    topic = data["topic"]
    main_title = data["title"]

    print("Topic:", topic)
    print("Main title:", main_title)

    publish_day = get_next_publish_day()

    print("Publish day:", publish_day)
    print("Timezone: Europe/Istanbul")

    # -----------------------------------------------------
    # SCHEDULE
    # -----------------------------------------------------

    short_1_time = turkey_to_utc(
        publish_day,
        9,
        0,
    )

    main_time = turkey_to_utc(
        publish_day,
        12,
        0,
    )

    short_2_time = turkey_to_utc(
        publish_day,
        21,
        0,
    )

    print()
    print("SCHEDULE")
    print("------------------------------------------")
    print("Short #1 :", short_1_time, "UTC")
    print("Main     :", main_time, "UTC")
    print("Short #2 :", short_2_time, "UTC")
    print("------------------------------------------")

    # -----------------------------------------------------
    # TAGS
    # -----------------------------------------------------

    base_tags = [
        "Shadow Archive",
        "mystery",
        "unsolved mystery",
        "unsolved cases",
        "real mystery",
        "true mystery",
        "gizem",
        "gizemli olaylar",
        "çözülemeyen olaylar",
        "gerçek olaylar",
    ]

    # =====================================================
    # SHORT #1
    # =====================================================

    short_1_title = f"{topic} — Gerçeği Ortaya Çıkaran Detay #Shorts"

    upload_video(
        SHORT_1,
        short_1_title,
        build_short_description(data, 1),
        short_1_time,
        base_tags + ["Shorts"],
    )

    # =====================================================
    # MAIN VIDEO
    # =====================================================

    upload_video(
        MAIN_VIDEO,
        main_title,
        build_main_description(data),
        main_time,
        base_tags,
    )

    # =====================================================
    # SHORT #2
    # =====================================================

    short_2_title = f"{topic} — Hâlâ Cevaplanamayan Soru #Shorts"

    upload_video(
        SHORT_2,
        short_2_title,
        build_short_description(data, 2),
        short_2_time,
        base_tags + ["Shorts"],
    )

    # =====================================================
    # COMPLETE
    # =====================================================

    print()
    print("==========================================")
    print("SHADOW ARCHIVE — YAYINLAR PLANLANDI")
    print("==========================================")
    print(f"📱 Short #1 : 09:00 Türkiye")
    print(f"🎬 Ana Video : 12:00 Türkiye")
    print(f"📱 Short #2 : 21:00 Türkiye")
    print()
    print("YouTube planlama tamamlandı.")
    print("==========================================")


if __name__ == "__main__":
    main()
