import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from google import genai


GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

MODEL = "gemini-3.6-flash"

TOPIC_FILE = Path("research/current_topic.json")


def telegram(method, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

    encoded = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def generate_topic():

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    prompt = """
You are the topic director for Shadow Archive.

Shadow Archive is a Turkish YouTube documentary channel focused on:

- mysterious real events
- unsolved cases
- disappearances
- unexplained historical events
- strange disasters
- abandoned places
- missing ships
- missing people
- historical mysteries

Generate ONE strong documentary topic.

IMPORTANT:

The topic must:
- be based on a real event
- have enough reliable information for a 15+ minute documentary
- have strong curiosity potential
- have a clear timeline
- contain enough people, locations and events to research
- avoid fabricated claims
- avoid conspiracy presented as fact
- avoid misleading clickbait
- preferably be less overused than extremely famous cases

The documentary should be possible to research using reliable web sources.

Return ONLY valid JSON.

Required format:

{
  "topic": "...",
  "category": "...",
  "summary": "...",
  "research_points": [
    "...",
    "...",
    "...",
    "...",
    "..."
  ],
  "title": "...",
  "description": "...",
  "hashtags": [
    "#...",
    "#...",
    "#...",
    "#...",
    "#..."
  ]
}

The title should be highly clickable but factual.

The description must be suitable for YouTube.

The hashtags must be directly related to the topic.

Do not use spam hashtags.

Do not add markdown.

Return JSON only.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    data = json.loads(text)

    required_fields = [
        "topic",
        "category",
        "summary",
        "research_points",
        "title",
        "description",
        "hashtags"
    ]

    for field in required_fields:
        if field not in data:
            raise RuntimeError(
                f"Gemini çıktısında eksik alan: {field}"
            )

    return data


def save_current_topic(data):

    TOPIC_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    TOPIC_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("==========================================")
    print("CURRENT TOPIC SAVED")
    print("==========================================")
    print(f"File: {TOPIC_FILE}")
    print(f"Topic: {data['topic']}")
    print(f"Title: {data['title']}")
    print("==========================================")


def send_telegram(data):

    hashtags = " ".join(data["hashtags"])

    research_points = "\n".join(
        f"• {point}"
        for point in data["research_points"]
    )

    message = (
        "🎬 SHADOW ARCHIVE — YENİ VİDEO\n\n"

        f"📌 KONU\n"
        f"{data['topic']}\n\n"

        f"🏷️ KATEGORİ\n"
        f"{data['category']}\n\n"

        f"📖 KONU ÖZETİ\n"
        f"{data['summary']}\n\n"

        f"🔎 ARAŞTIRMA NOKTALARI\n"
        f"{research_points}\n\n"

        f"📝 BAŞLIK\n"
        f"{data['title']}\n\n"

        f"📄 AÇIKLAMA\n"
        f"{data['description']}\n\n"

        f"🏷️ ETİKETLER\n"
        f"{hashtags}\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "Video üretimine geçilsin mi?"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ ONAYLA",
                    "callback_data": "topic_approve"
                },
                {
                    "text": "❌ REDDET",
                    "callback_data": "topic_reject"
                }
            ],
            [
                {
                    "text": "🕐 SAATİ DEĞİŞTİR",
                    "callback_data": "change_time"
                }
            ]
        ]
    }

    telegram(
        "sendMessage",
        {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "reply_markup": json.dumps(keyboard)
        }
    )

    print("==========================================")
    print("SHADOW ARCHIVE TOPIC SENT")
    print("==========================================")
    print("Topic:", data["topic"])
    print("Title:", data["title"])
    print("==========================================")


def main():

    print("==========================================")
    print("SHADOW ARCHIVE DAILY TOPIC SYSTEM")
    print("==========================================")

    data = generate_topic()

    save_current_topic(data)

    send_telegram(data)

    print("DAILY TOPIC COMPLETED")


if __name__ == "__main__":
    main()
