import json
import os
from pathlib import Path

from google import genai


GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-3.6-flash"

TOPIC_FILE = Path("research/current_topic.json")
HISTORY_FILE = Path("research/topic_history.json")


# ============================================================
# SHADOW ARCHIVE — KONU KURALLARI
# ============================================================

FORBIDDEN_CATEGORIES = [
    "ship",
    "ships",
    "boat",
    "boats",
    "vessel",
    "vessels",
    "aircraft",
    "airplane",
    "airplane disappearance",
    "aircraft disappearance",
    "plane",
    "planes",
    "aviation",
    "airship",
    "zeppelin",
    "blimp",
    "dirigible",
    "submarine",
    "uçak",
    "uçak kaybolması",
    "gemi",
    "gemi kaybolması",
    "zeplin",
    "hava gemisi",
    "denizaltı",
]

FORBIDDEN_KEYWORDS = [
    "mv joyita",
    "joyita",
    "boeing 727",
    "luanda",
    "n844aa",
]


def normalize(text):
    return (
        str(text)
        .lower()
        .strip()
        .replace("’", "'")
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def load_previous_topics():
    topics = []

    # --------------------------------------------------------
    # Mevcut konu
    # --------------------------------------------------------

    if TOPIC_FILE.exists():

        try:

            with open(
                TOPIC_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            topic = data.get(
                "topic",
                ""
            ).strip()

            if topic:
                topics.append(topic)

        except Exception as e:

            print(
                f"Mevcut konu okunamadı: {e}"
            )

    # --------------------------------------------------------
    # Konu geçmişi
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Tekilleştir
    # --------------------------------------------------------

    result = []
    seen = set()

    for topic in topics:

        normalized = normalize(topic)

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
        for topic in previous_topics[-100:]
    )

    if not previous_text:

        previous_text = (
            "- Henüz konu geçmişi yok."
        )

    prompt = f"""
You are the senior topic director for Shadow Archive,
a professional Turkish YouTube documentary channel.

Generate ONE completely NEW real-world documentary topic.

============================================================
ABSOLUTE BAN
============================================================

DO NOT generate any topic involving:

- ships
- boats
- vessels
- submarines
- aircraft
- airplanes
- planes
- aviation
- airships
- zeppelins
- blimps
- dirigibles

This means:

NO missing ships.
NO mysterious ships.
NO ship disasters.
NO missing aircraft.
NO airplane disappearances.
NO aviation mysteries.
NO zeppelin mysteries.
NO blimp mysteries.

Also NEVER generate:

- MV Joyita
- Joyita
- Boeing 727 disappearance
- Luanda Boeing 727
- N844AA

============================================================
IMPORTANT
============================================================

The topic must be substantially different from every topic
in the previous-topic list.

Do NOT create a new wording for an old event.

For example:

If an old topic is about a particular person,
you cannot create another title about the same person.

If an old topic is about a particular disaster,
you cannot create another version of the same disaster.

============================================================
PREFERRED TOPIC TYPES
============================================================

Choose from areas such as:

- mysterious people
- unexplained disappearances of people
- strange historical events
- abandoned buildings
- mysterious locations
- unexplained archaeological discoveries
- strange inventions
- mysterious photographs
- unexplained signals
- strange experiments
- unusual scientific incidents
- secret historical operations
- unexplained deaths
- mysterious letters
- strange recordings
- historical crimes
- unsolved investigations
- bizarre accidents that do NOT involve aircraft, ships,
  boats, vessels, submarines, zeppelins or blimps
- abandoned towns
- underground structures
- mysterious objects
- unusual discoveries
- historical mysteries

============================================================
QUALITY REQUIREMENTS
============================================================

The event MUST:

- be real
- be researchable
- have reliable sources
- have enough information for a 15+ minute documentary
- have a clear timeline
- have several research points
- have strong visual potential
- have genuine mystery or curiosity
- not depend on fabricated claims
- not present conspiracy theories as established facts
- preferably be obscure rather than extremely overused

============================================================
PREVIOUS TOPICS — FORBIDDEN
============================================================

{previous_text}

============================================================
OUTPUT
============================================================

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

The title must be clickable but factual.

The description must be suitable for YouTube.

Hashtags must be directly related to the topic.

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


def is_forbidden(data):

    topic = normalize(
        data.get("topic", "")
    )

    title = normalize(
        data.get("title", "")
    )

    category = normalize(
        data.get("category", "")
    )

    summary = normalize(
        data.get("summary", "")
    )

    combined = (
        f"{topic} {title} "
        f"{category} {summary}"
    )

    # --------------------------------------------------------
    # Yasaklı özel olaylar
    # --------------------------------------------------------

    for keyword in FORBIDDEN_KEYWORDS:

        if normalize(keyword) in combined:

            print(
                f"❌ YASAKLI KONU: {keyword}"
            )

            return True

    # --------------------------------------------------------
    # Yasaklı ulaşım türleri
    # --------------------------------------------------------

    for keyword in FORBIDDEN_CATEGORIES:

        if normalize(keyword) in combined:

            print(
                f"❌ YASAKLI KATEGORİ: {keyword}"
            )

            return True

    return False


def is_duplicate(
    data,
    previous_topics
):

    new_topic = normalize(
        data.get(
            "topic",
            ""
        )
    )

    new_title = normalize(
        data.get(
            "title",
            ""
        )
    )

    if not new_topic:
        return True

    for old_topic in previous_topics:

        old_normalized = normalize(
            old_topic
        )

        if not old_normalized:
            continue

        # Tam eşleşme
        if new_topic == old_normalized:

            print(
                "❌ DUPLICATE: Tam konu eşleşmesi."
            )

            return True

        # Başlığın eski konuyla aynı olması
        if new_title == old_normalized:

            print(
                "❌ DUPLICATE: Başlık eski konuyla aynı."
            )

            return True

        # Çok güçlü kelime çakışması
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

        if len(common_words) >= 4:

            print(
                "❌ DUPLICATE: Güçlü konu benzerliği."
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
    print(
        "=========================================="
    )
    print(
        "CURRENT TOPIC SAVED"
    )
    print(
        "=========================================="
    )

    print(
        f"File: {TOPIC_FILE}"
    )

    print(
        f"Topic: {data['topic']}"
    )

    print(
        f"Title: {data['title']}"
    )

    print(
        "=========================================="
    )


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


def main():

    print(
        "=========================================="
    )

    print(
        "SHADOW ARCHIVE DAILY TOPIC SYSTEM"
    )

    print(
        "=========================================="
    )

    previous_topics = load_previous_topics()

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
    print(
        "🚫 GEMİ / UÇAK / ZEPLİN KONULARI ENGELLİ"
    )

    print("")
    print(
        "YENİ KONU ÜRETİLİYOR..."
    )

    print("")

    data = None

    # 10 deneme
    for attempt in range(1, 11):

        print(
            f"KONU ÜRETİM DENEMESİ: {attempt}/10"
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

            if attempt == 10:

                raise

            print(
                "Yeni deneme yapılacak..."
            )

            print("")

            continue

        print(
            f"ÜRETİLEN KONU: {candidate['topic']}"
        )

        # Yasak kontrolü
        if is_forbidden(candidate):

            print(
                "❌ YASAKLI KONU ÜRETİLDİ."
            )

            print(
                "Yeni konu isteniyor..."
            )

            print("")

            continue

        # Tekrar kontrolü
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
            "10 denemede de uygun yeni konu üretilemedi."
        )

    save_current_topic(
        data
    )

    save_history(
        data
    )

    print("")
    print(
        "ℹ️ TOPIC TELEGRAM MESAJI GÖNDERİLMEDİ."
    )

    print("")
    print(
        "=========================================="
    )

    print(
        "DAILY TOPIC COMPLETED"
    )

    print(
        "=========================================="
    )

    print(
        f"KONU: {data['topic']}"
    )

    print(
        f"BAŞLIK: {data['title']}"
    )

    print(
        f"AÇIKLAMA: {data['description']}"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
