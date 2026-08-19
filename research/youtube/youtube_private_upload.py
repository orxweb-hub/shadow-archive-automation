import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# SHADOW ARCHIVE — YOUTUBE PRIVATE UPLOADER
# ============================================================

TOPIC_FILE = Path("production_package/research/current_topic.json")
METADATA_FILE = Path("production_package/metadata/production.json")

MAIN_VIDEO = Path("production_package/main/main_video.mp4")
SHORT_1 = Path("production_package/shorts/short_1.mp4")
SHORT_2 = Path("production_package/shorts/short_2.mp4")

TURKEY = ZoneInfo("Europe/Istanbul")

CLIENT_JSON = os.environ["YOUTUBE_OAUTH_CLIENT_JSON"]
REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]

print("=" * 60)
print("SHADOW ARCHIVE — YOUTUBE PRIVATE UPLOADER")
print("=" * 60)


# ============================================================
# GOOGLE OAUTH
# ============================================================

client = json.loads(CLIENT_JSON)

client_data = client.get("web") or client.get("installed")

if not client_data:
    raise RuntimeError(
        "YOUTUBE_OAUTH_CLIENT_JSON içinde web veya installed bulunamadı."
    )

credentials = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_data["client_id"],
    client_secret=client_data["client_secret"],
    scopes=[
        "https://www.googleapis.com/auth/youtube"
    ],
)

youtube = build(
    "youtube",
    "v3",
    credentials=credentials,
)


# ============================================================
# DOSYA KONTROLÜ
# ============================================================

def check_files():
    print("\n📁 DOSYA KONTROLÜ")

    files = [
        TOPIC_FILE,
        MAIN_VIDEO,
        SHORT_1,
        SHORT_2,
    ]

    for file in files:
        print(f"Kontrol: {file}")

        if not file.exists():
            raise FileNotFoundError(
                f"Dosya bulunamadı: {file}"
            )

        size_mb = file.stat().st_size / (1024 * 1024)

        print(
            f"✅ {file.name} | {size_mb:.2f} MB"
        )

    if METADATA_FILE.exists():
        print(f"✅ Metadata bulundu: {METADATA_FILE}")
    else:
        print("ℹ️ Metadata dosyası bulunamadı, devam ediliyor.")


# ============================================================
# TOPIC
# ============================================================

def load_topic():
    if not TOPIC_FILE.exists():
        raise FileNotFoundError(
            f"current_topic.json bulunamadı: {TOPIC_FILE}"
        )

    with open(
        TOPIC_FILE,
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    title = data.get(
        "title",
        data.get(
            "topic",
            "Shadow Archive"
        )
    )

    description = data.get(
        "description",
        ""
    )

    hashtags = data.get(
        "hashtags",
        []
    )

    if isinstance(hashtags, list):
        hashtag_text = " ".join(
            str(x) for x in hashtags
        )
    else:
        hashtag_text = str(hashtags)

    return {
        "topic": data.get(
            "topic",
            "Shadow Archive"
        ),
        "title": title,
        "description": description,
        "hashtags": hashtag_text,
    }


# ============================================================
# YAYIN GÜNÜ
# ============================================================

def get_publish_day():
    """
    Türkiye saati:

    Short 1 → 09:00
    Ana Video → 12:00
    Short 2 → 21:00

    Onay 09:00'dan önceyse:
        bugün

    09:00 veya sonrasındaysa:
        yarın
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

    return (
        now + timedelta(days=1)
    ).date()


# ============================================================
# TÜRKİYE → UTC
# ============================================================

def turkey_to_utc(
    date_value,
    hour,
    minute,
):
    turkey_time = datetime(
        date_value.year,
        date_value.month,
        date_value.day,
        hour,
        minute,
        tzinfo=TURKEY,
    )

    utc_time = turkey_time.astimezone(
        timezone.utc
    )

    return utc_time.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


# ============================================================
# DESCRIPTION
# ============================================================

def build_description(
    description,
    hashtags,
):
    text = description.strip()

    if hashtags:
        text += "\n\n" + hashtags

    return text[:5000]


# ============================================================
# UPLOAD
# ============================================================

def upload_video(
    video_path,
    title,
    description,
    publish_at,
    is_short=False,
):
    print("\n" + "=" * 60)
    print("YOUTUBE UPLOAD BAŞLIYOR")
    print("=" * 60)

    print(f"Video: {video_path}")
    print(f"Başlık: {title}")
    print(f"Yayın zamanı UTC: {publish_at}")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "24",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            progress = int(
                status.progress() * 100
            )

            print(
                f"Yükleme: {progress}%"
            )

    video_id = response.get("id")

    if not video_id:
        raise RuntimeError(
            f"YouTube video ID döndürmedi: {response}"
        )

    print("\n✅ YOUTUBE UPLOAD BAŞARILI")
    print(f"VIDEO ID: {video_id}")
    print(
        f"https://www.youtube.com/watch?v={video_id}"
    )

    return video_id


# ============================================================
# MAIN
# ============================================================

def main():

    check_files()

    topic = load_topic()

    print("\n" + "=" * 60)
    print("KONU")
    print("=" * 60)

    print(
        f"Topic: {topic['topic']}"
    )

    print(
        f"Title: {topic['title']}"
    )

    publish_day = get_publish_day()

    print("\n" + "=" * 60)
    print("YAYIN PLANI")
    print("=" * 60)

    print(
        f"Yayın günü: {publish_day}"
    )

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

    print(
        f"Short #1: {short_1_time}"
    )

    print(
        f"Ana Video: {main_time}"
    )

    print(
        f"Short #2: {short_2_time}"
    )

    description = build_description(
        topic["description"],
        topic["hashtags"],
    )

    # ========================================================
    # SHORT 1
    # ========================================================

    short_1_title = (
        f"{topic['title']} | #Shorts"
    )

    short_1_id = upload_video(
        video_path=SHORT_1,
        title=short_1_title,
        description=description,
        publish_at=short_1_time,
        is_short=True,
    )

    # ========================================================
    # MAIN VIDEO
    # ========================================================

    main_title = topic["title"]

    main_id = upload_video(
        video_path=MAIN_VIDEO,
        title=main_title,
        description=description,
        publish_at=main_time,
        is_short=False,
    )

    # ========================================================
    # SHORT 2
    # ========================================================

    short_2_title = (
        f"{topic['title']} | #Shorts"
    )

    short_2_id = upload_video(
        video_path=SHORT_2,
        title=short_2_title,
        description=description,
        publish_at=short_2_time,
        is_short=True,
    )

    # ========================================================
    # SONUÇ
    # ========================================================

    print("\n")
    print("=" * 60)
    print("🎉 SHADOW ARCHIVE YOUTUBE YAYINLARI HAZIR")
    print("=" * 60)

    print(
        f"Short #1 VIDEO ID: {short_1_id}"
    )

    print(
        f"Ana Video VIDEO ID: {main_id}"
    )

    print(
        f"Short #2 VIDEO ID: {short_2_id}"
    )

    print("\nYAYIN TAKVİMİ:")
    print(
        f"Short #1 → {publish_day} 09:00 Türkiye"
    )
    print(
        f"Ana Video → {publish_day} 12:00 Türkiye"
    )
    print(
        f"Short #2 → {publish_day} 21:00 Türkiye"
    )

    print("\n✅ TÜM VİDEOLAR YOUTUBE'A PRIVATE OLARAK YÜKLENDİ.")
    print("=" * 60)


if __name__ == "__main__":
    main()
