import os
import json
import time
import re
from pathlib import Path

from google import genai


TOPIC_FILE = Path(
    "research/current_topic.json"
)

REPORT_DIR = Path(
    "research/reports"
)

SCRIPT_DIR = Path(
    "research/scripts"
)

MIN_WORDS = 2700

MODEL = "gemini-3.6-flash"

MAX_RETRIES = 5

RETRY_DELAYS = [
    30,
    60,
    120,
    180,
    300
]


def get_client():

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY bulunamadı."
        )

    return genai.Client(
        api_key=api_key
    )


def load_topic():

    if not TOPIC_FILE.exists():

        raise FileNotFoundError(
            "Güncel konu dosyası bulunamadı: "
            f"{TOPIC_FILE}"
        )

    data = json.loads(
        TOPIC_FILE.read_text(
            encoding="utf-8"
        )
    )

    topic = data.get(
        "topic"
    )

    if not topic:

        raise RuntimeError(
            "current_topic.json içinde topic bulunamadı."
        )

    return data


def find_latest_report():

    reports = list(
        REPORT_DIR.glob(
            "*_web_research.json"
        )
    )

    if not reports:

        raise FileNotFoundError(
            "Web araştırma raporu bulunamadı."
        )

    reports.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    return reports[0]


def create_safe_filename(text):

    filename = text.lower()

    filename = re.sub(
        r"[^a-z0-9]+",
        "_",
        filename
    )

    filename = filename.strip("_")

    if not filename:

        filename = "daily_topic"

    return filename[:80]


def generate_script(
    client,
    topic_data,
    report
):

    topic = topic_data.get(
        "topic",
        ""
    )

    category = topic_data.get(
        "category",
        ""
    )

    suggested_title = topic_data.get(
        "title",
        ""
    )

    prompt = f"""
You are the senior documentary writer for the YouTube channel
"Shadow Archive".

Write a professional, original Turkish documentary narration
about this real-world mystery:

TOPIC:
{topic}

CATEGORY:
{category}

SUGGESTED TITLE:
{suggested_title}

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

TARGET LENGTH:
2,700–3,200 Turkish words.

IMPORTANT:
The narration MUST aim for at least 2,700 words in a SINGLE
generation.

FACTUAL RULES:

- Use only information supported by the research report.
- Never invent facts.
- Never invent dialogue.
- Never invent witnesses.
- Never invent evidence.
- Never invent events.
- Never present rumors as confirmed facts.
- Clearly separate confirmed facts from theories.
- If something is uncertain, explain that it is uncertain.
- Do not repeat information simply to increase length.
- Do not treat atmospheric stock footage as historical evidence.

STYLE:

- Natural Turkish.
- Serious investigative documentary.
- Strong opening.
- Gradually increasing suspense.
- Natural transitions.
- Varied sentence lengths.
- Clear and natural narration.
- No repetitive AI-style phrases.
- No excessive clickbait.
- Every paragraph should provide useful information.

COVER:

- Background of the event.
- Important people and locations.
- Events before the mystery.
- The disappearance or incident.
- Discovery or investigation.
- Physical evidence.
- Missing people if applicable.
- Official investigation.
- Official findings.
- Major theories.
- Problems and contradictions with those theories.
- What remains unexplained.
- Strong final conclusion.

STRUCTURE:

1. Strong opening and mystery
2. Background
3. Events before the incident
4. The disappearance or main event
5. Discovery
6. Evidence
7. People involved
8. Investigation
9. Official findings
10. Major theories
11. Problems and contradictions
12. What remains unexplained
13. Final conclusion

Do not add filler.

Do not repeat the same facts.

Do not invent information just to reach the word count.

Write ONLY the finished Turkish narration.

Do not include:

- headings
- bullet points
- timestamps
- camera directions
- sound effects
- editing instructions
- production notes
"""


    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                "Gemini senaryo üretimi "
                f"denemesi {attempt}/{MAX_RETRIES}"
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            text = response.text.strip()

            if not text:

                raise RuntimeError(
                    "Gemini boş senaryo döndürdü."
                )

            print(
                "Gemini senaryo üretimi başarılı."
            )

            return text

        except Exception as error:

            error_text = str(error)

            print()
            print(
                "Gemini hatası:"
            )
            print(error)

            # 429 = günlük kota / rate limit.
            # Tekrar denemiyoruz.

            if (
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED"
                in error_text
                or
                "quota"
                in error_text.lower()
            ):

                raise RuntimeError(
                    "Gemini kotası dolu veya rate limit "
                    "aşıldı. Tekrar denenmeyecek."
                ) from error

            # 503 = geçici servis yoğunluğu.

            if (
                "503" in error_text
                or
                "UNAVAILABLE"
                in error_text
                or
                "high demand"
                in error_text.lower()
            ):

                if attempt == MAX_RETRIES:

                    raise RuntimeError(
                        "Gemini 503 hatası "
                        f"{MAX_RETRIES} denemede "
                        "de çözülemedi."
                    ) from error

                delay = RETRY_DELAYS[
                    attempt - 1
                ]

                print(
                    f"Gemini yoğun. "
                    f"{delay} saniye bekleniyor..."
                )

                time.sleep(
                    delay
                )

                continue

            # Diğer geçici hatalar.

            if attempt == MAX_RETRIES:

                raise RuntimeError(
                    "Gemini senaryo üretimi "
                    f"{MAX_RETRIES} denemede başarısız."
                ) from error

            delay = RETRY_DELAYS[
                attempt - 1
            ]

            print(
                f"{delay} saniye bekleniyor..."
            )

            time.sleep(
                delay
            )

    raise RuntimeError(
        "Gemini senaryo üretilemedi."
    )


def main():

    print(
        "SHADOW ARCHIVE — LONG SCRIPT GENERATOR"
    )

    print("=" * 60)

    topic_data = load_topic()

    topic = topic_data["topic"]

    print(
        "GÜNCEL KONU:"
    )

    print(topic)

    print()

    report_file = find_latest_report()

    print(
        "ARAŞTIRMA RAPORU:"
    )

    print(report_file)

    print()

    report = json.loads(
        report_file.read_text(
            encoding="utf-8"
        )
    )

    client = get_client()

    print(
        "Uzun Türkçe senaryo oluşturuluyor..."
    )

    script = generate_script(
        client,
        topic_data,
        report
    )

    word_count = len(
        script.split()
    )

    print()

    print(
        f"Senaryo kelime sayısı: "
        f"{word_count}"
    )

    if word_count < MIN_WORDS:

        raise RuntimeError(
            f"Senaryo 2700 kelimenin altında kaldı: "
            f"{word_count}"
        )

    SCRIPT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_name = create_safe_filename(
        topic
    )

    script_file = (
        SCRIPT_DIR /
        f"{safe_name}_script.txt"
    )

    script_file.write_text(
        script,
        encoding="utf-8"
    )

    print()
    print("=" * 60)

    print(
        "SENARYO BAŞARIYLA HAZIRLANDI"
    )

    print("=" * 60)

    print(
        f"Konu: {topic}"
    )

    print(
        f"Kelime sayısı: {word_count}"
    )

    print(
        f"Dosya: {script_file}"
    )

    print(
        "Gemini başarılı üretim: 1"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
