import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from google import genai


GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

MODEL = "gemini-3.6-flash"

TOPIC_FILE = Path("research/current_topic.json")
HISTORY_FILE = Path("research/topic_history.json")


def telegram(method, data):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram devre dışı.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

    encoded = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode())

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API hatası: {result}"
        )

    return result


def load_previous_topics():
    topics = []

    # Mevcut konu
    if TOPIC_FILE.exists():
        try:
            with open(
                TOPIC_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            topic = data.get("topic", "").strip()

            if topic:
                topics.append(topic)

        except Exception as e:
            print(
                f"Mevcut konu okunamadı: {e}"
            )

    # Konu geçmişi
    if HISTORY_FILE.exists():
        try:
            with open(
                HISTORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                history = json.load(f)

            if isinstance(history, list):
                for item in history:
                    if isinstance(item, str):
                        topics.append(item)

                    elif isinstance(item, dict):
                        topic = item.get(
                            "topic",
                            ""
                        )

                        if topic:
                            topics.append(
                                topic
                            )

        except Exception as e:
            print(
                f"Konu geçmişi okunamadı: {e}"
            )

    # Tekilleştir
    result = []

    seen = set()

    for topic in topics:
        normalized = topic.lower().strip()

        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(topic)

    return result


def generate_topic(previous_topics):
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    previous_text = "\n".join(
        f"- {topic}"
        for topic in previous_topics[-30:]
    )

    if not previous_text:
        previous_text = "- Henüz konu geçmişi yok."

    prompt = f"""
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
- aviation mysteries
- strange accidents

Your job is to generate ONE completely NEW documentary topic.

CRITICAL RULE:

The new topic MUST NOT be the same event, case, person,
ship, aircraft, disaster, disappearance or mystery as any
topic in the previous-topic list.

Do NOT create another title about the same event using
different wording.

For example:

If "L-8 Ghost Blimp Disappearance" appears in the previous
topics, you MUST NOT generate:

- L-8 Ghost Blimp
- L-8 Disappearance
- The Ghost Blimp
- The Vanishing L-8 Crew
- 1942 L-8 Mystery

These are all the SAME event and are forbidden.

Choose a genuinely different real event.

PREVIOUS TOPICS — ABSOLUTELY FORBIDDEN:

{previous_text}

The new topic must:

- be based on a real historical event
- have enough reliable information for a 15+ minute documentary
- have a strong curiosity factor
- have a clear timeline
- contain enough people, locations and events to research
- be researchable using reliable sources
- avoid fabricated claims
- avoid conspiracy presented as fact
- avoid misleading clickbait
- preferably be less overused than extremely famous cases
- be substantially different from all previous topics

Try to choose a topic from a different case/event than the
previous video.

Return ONLY valid JSON.

Required format:

{{
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
}}

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
        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

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


def is_duplicate(data, previous_topics):
    new_topic = data.get(
        "topic",
        ""
    ).strip().lower()

    new_title = data.get(
        "title",
        ""
    ).strip().lower()

    for old_topic in previous_topics:
        old_normalized = old_topic.strip().lower()

        if not old_normalized:
            continue

        # Direkt eşleşme
        if new_topic == old_normalized:
            return True

        # Çok belirgin aynı olay kontrolü
        new_words = set(
            new_topic.split()
        )

        old_words = set(
            old_normalized.split()
        )

        common = new_words.intersection(
            old_words
        )

        if len(common) >= 4:
            return True

        # Başlıkta da eski olayın adı geçiyorsa
        old_title_words = set(
            old_normalized.split()
        )

        title_common = set(
            new_title.split()
        ).intersection(
            old_title_words
        )

        if len(title_common) >= 4:
            return True

    return False


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
    print(
        f"File: {TOPIC_FILE}"
    )
    print(
        f"Topic: {data['topic']}"
    )
    print(
        f"Title: {data['title']}"
    )
    print("==========================================")


def save_history(data):
    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    history = []

    if HISTORY_FILE.exists():
        try:
            with open(
                HISTORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                history = json.load(f)

            if not isinstance(history, list):
                history = []

        except Exception:
            history = []

    history.append(
        {
            "topic": data["topic"],
            "title": data["title"]
        }
    )

    # Son 100 konuyu tut
    history = history[-100:]

    HISTORY_FILE.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Topic history updated: {len(history)} topics"
    )


def send_telegram(data):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "Telegram gönderimi atlandı."
        )
        return

    hashtags = " ".join(
        data["hashtags"]
    )

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
            "reply_markup": json.dumps(
                keyboard,
                ensure_ascii=False
            )
        }
    )

    print(
        "Telegram topic message sent."
    )


def main():
    print("==========================================")
    print("SHADOW ARCHIVE DAILY TOPIC SYSTEM")
    print("==========================================")

    previous_topics = load_previous_topics()

    print("")
    print(
        f"ÖNCEKİ KONU SAYISI: {len(previous_topics)}"
    )

    if previous_topics:
        print("")
        print("SON KONULAR:")
        for topic in previous_topics[-10:]:
            print(
                f"- {topic}"
            )

    print("")
    print("YENİ KONU ÜRETİLİYOR...")
    print("")

    data = None

    # Aynı konu gelirse en fazla 5 kez yeniden üret
    for attempt in range(1, 6):
        print(
            f"KONU ÜRETİM DENEMESİ: {attempt}/5"
        )

        candidate = generate_topic(
            previous_topics
        )

        print(
            f"ÜRETİLEN KONU: {candidate['topic']}"
        )

        if is_duplicate(
            candidate,
            previous_topics
        ):
            print(
                "❌ BU KONU DAHA ÖNCE KULLANILMIŞ."
            )
            print(
                "Yeni konu tekrar isteniyor..."
            )
            print("")
            continue

        data = candidate

        print(
            "✅ YENİ VE FARKLI KONU BULUNDU."
        )
        break

    if data is None:
        raise RuntimeError(
            "5 denemede de yeni ve farklı konu üretilemedi."
        )

    save_current_topic(data)

    save_history(data)

    send_telegram(data)

    print("")
    print("==========================================")
    print("DAILY TOPIC COMPLETED")
    print("==========================================")
    print(
        f"KONU: {data['topic']}"
    )
    print(
        f"BAŞLIK: {data['title']}"
    )
    print("==========================================")


if __name__ == "__main__":
    main()
