import json
import os
from pathlib import Path

from google import genai


GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-3.6-flash"

TOPIC_FILE = Path("research/current_topic.json")
HISTORY_FILE = Path("research/topic_history.json")


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
                        topic = item.strip()

                        if topic:
                            topics.append(topic)

                    elif isinstance(item, dict):
                        topic = item.get(
                            "topic",
                            ""
                        ).strip()

                        if topic:
                            topics.append(topic)

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
        for topic in previous_topics[-50:]
    )

    if not previous_text:
        previous_text = "- Henüz konu geçmişi yok."

    prompt = f"""
You are the topic director for Shadow Archive.

Shadow Archive is a Turkish YouTube documentary channel.

The channel covers:

- mysterious real events
- unsolved cases
- disappearances
- unexplained historical events
- strange disasters
- abandoned places
- missing ships
- missing people
- aviation mysteries
- strange accidents
- historical mysteries

Your task is to generate ONE completely NEW documentary topic.

IMPORTANT:

The new topic MUST be a genuinely different real-world
event from every topic in the previous-topic list.

Do NOT generate the same event with different wording.

If an aircraft, ship, person, disaster or disappearance
already appears in the previous topics, that exact event
is forbidden.

For example:

If L-8 Ghost Blimp is in the previous topics, you MUST NOT
generate:

- L-8 Ghost Blimp
- L-8 Disappearance
- Ghost Blimp Mystery
- Vanishing L-8 Crew
- 1942 L-8 Mystery

All of those refer to the same event.

Choose a completely different event.

PREVIOUS TOPICS — FORBIDDEN:

{previous_text}

The new topic must:

- be a real historical event
- have reliable sources
- have enough information for a 15+ minute documentary
- have a clear timeline
- have enough people, locations and events to research
- have strong curiosity potential
- avoid fabricated claims
- avoid conspiracy presented as fact
- avoid misleading clickbait
- preferably not be an extremely overused case
- be substantially different from all previous topics

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

Rules:

The title must be highly clickable but factual.

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

    # Markdown JSON temizleme
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

    # Alanların boş olup olmadığını kontrol et
    for field in [
        "topic",
        "category",
        "summary",
        "title",
        "description"
    ]:

        if not str(
            data[field]
        ).strip():

            raise RuntimeError(
                f"Gemini çıktısında boş alan: {field}"
            )

    if not isinstance(
        data["research_points"],
        list
    ):
        raise RuntimeError(
            "research_points liste değil."
        )

    if not isinstance(
        data["hashtags"],
        list
    ):
        raise RuntimeError(
            "hashtags liste değil."
        )

    return data


def is_duplicate(
    data,
    previous_topics
):

    new_topic = data.get(
        "topic",
        ""
    ).strip().lower()

    new_title = data.get(
        "title",
        ""
    ).strip().lower()

    if not new_topic:
        return True

    for old_topic in previous_topics:

        old_normalized = (
            old_topic
            .strip()
            .lower()
        )

        if not old_normalized:
            continue

        # Tam eşleşme
        if new_topic == old_normalized:
            print(
                "DUPLICATE: Tam konu eşleşmesi."
            )
            return True

        new_words = set(
            new_topic.split()
        )

        old_words = set(
            old_normalized.split()
        )

        common_words = (
            new_words.intersection(
                old_words
            )
        )

        # Çok güçlü kelime çakışması
        if len(common_words) >= 4:

            print(
                "DUPLICATE: Güçlü konu benzerliği."
            )

            return True

        title_words = set(
            new_title.split()
        )

        title_common = (
            title_words.intersection(
                old_words
            )
        )

        if len(title_common) >= 4:

            print(
                "DUPLICATE: Başlık benzerliği."
            )

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

    print("")
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

            if not isinstance(
                history,
                list
            ):
                history = []

        except Exception:

            history = []

    history.append(
        {
            "topic": data["topic"],
            "title": data["title"]
        }
    )

    # Son 100 konuyu sakla
    history = history[-100:]

    HISTORY_FILE.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("")
    print(
        f"Topic history updated: {len(history)} topics"
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

    # Aynı konu gelirse maksimum 5 deneme
    for attempt in range(1, 6):

        print(
            f"KONU ÜRETİM DENEMESİ: {attempt}/5"
        )

        try:

            candidate = generate_topic(
                previous_topics
            )

        except Exception as e:

            print("")
            print(
                f"❌ GEMINI HATASI: {e}"
            )

            if attempt == 5:
                raise

            print(
                "Yeni deneme yapılacak..."
            )
            print("")

            continue

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
                "Yeni konu isteniyor..."
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

    save_current_topic(
        data
    )

    save_history(
        data
    )

    # Telegram burada KESİNLİKLE gönderilmiyor.
    #
    # Telegram yayın onayı ayrı workflow tarafından
    # gönderilecek.
    print("")
    print(
        "ℹ️ TOPIC TELEGRAM MESAJI GÖNDERİLMEDİ."
    )

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

    print(
        f"AÇIKLAMA: {data['description']}"
    )

    print("==========================================")


if __name__ == "__main__":
    main()
