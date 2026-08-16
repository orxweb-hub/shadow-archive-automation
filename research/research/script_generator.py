import os
import json
import time
import re
from pathlib import Path

from google import genai


TOPIC_FILE = Path("research/current_topic.json")
REPORT_DIR = Path("research/reports")
SCRIPT_DIR = Path("research/scripts")

MIN_WORDS = 2700
MAX_WORDS = 3400

MODEL = "gemini-3.5-flash-lite"

MAX_RETRIES = 5

RETRY_DELAYS = [
    30,
    60,
    120,
    180,
    300
]


def get_client():

    api_key = os.environ.get("GEMINI_API_KEY")

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

    topic = data.get("topic")

    if not topic:
        raise RuntimeError(
            "current_topic.json içinde topic bulunamadı."
        )

    return data


def find_latest_report():

    reports = list(
        REPORT_DIR.glob("*_web_research.json")
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


def call_gemini(client, prompt):

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"Gemini isteği "
                f"{attempt}/{MAX_RETRIES}"
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            text = (
                response.text.strip()
                if response.text
                else ""
            )

            if not text:
                raise RuntimeError(
                    "Gemini boş cevap döndürdü."
                )

            print(
                "Gemini üretimi başarılı."
            )

            return text

        except Exception as error:

            error_text = str(error)

            print()
            print("Gemini hatası:")
            print(error)

            if (
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED" in error_text
                or
                "quota" in error_text.lower()
            ):

                raise RuntimeError(
                    "Gemini kotası dolu veya rate limit "
                    "aşıldı."
                ) from error

            if (
                "503" in error_text
                or
                "UNAVAILABLE" in error_text
                or
                "high demand" in error_text.lower()
            ):

                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        "Gemini 503 hatası çözülemedi."
                    ) from error

                delay = RETRY_DELAYS[
                    attempt - 1
                ]

                print(
                    f"{delay} saniye bekleniyor..."
                )

                time.sleep(delay)

                continue

            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    "Gemini senaryo üretimi başarısız."
                ) from error

            delay = RETRY_DELAYS[
                attempt - 1
            ]

            print(
                f"{delay} saniye bekleniyor..."
            )

            time.sleep(delay)

    raise RuntimeError(
        "Gemini cevap üretemedi."
    )


def generate_initial_script(
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
about this real-world mystery.

TOPIC:
{topic}

CATEGORY:
{category}

SUGGESTED TITLE:
{suggested_title}

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

LENGTH REQUIREMENT:

Write BETWEEN 2,700 and 3,200 Turkish words.

This requirement is mandatory.

Aim for approximately 3,000 words.

Do NOT stop at 2,000 words.

Do NOT stop at 2,200 words.

Do NOT stop at 2,500 words.

Continue developing the investigation naturally until the
narration reaches approximately 3,000 words.

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
- Do not use filler.

STYLE:

- Natural Turkish.
- Serious investigative documentary.
- Strong opening.
- Gradually increasing suspense.
- Natural transitions.
- Varied sentence lengths.
- Clear narration.
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

    return call_gemini(
        client,
        prompt
    )


def expand_script(
    client,
    script,
    topic,
    report,
    current_words
):

    missing_words = MIN_WORDS - current_words

    print()
    print(
        f"Senaryo kısa kaldı: "
        f"{current_words} kelime"
    )

    print(
        f"Eksik yaklaşık: "
        f"{missing_words} kelime"
    )

    prompt = f"""
You are editing a Turkish investigative documentary
for the YouTube channel "Shadow Archive".

The current narration is too short.

TOPIC:
{topic}

CURRENT WORD COUNT:
{current_words}

MINIMUM REQUIRED WORD COUNT:
{MIN_WORDS}

The narration must reach at least 2,700 words.

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

CURRENT NARRATION:
{script}

TASK:

Expand the narration naturally.

Add approximately
{max(missing_words + 200, 700)}
new Turkish words.

Do NOT rewrite the entire story from zero.

Keep the existing useful information.

Add factual depth using only the research report.

Useful expansion areas include:

- historical background
- chronology
- people involved
- locations
- investigation details
- physical evidence
- official findings
- competing theories
- contradictions
- unanswered questions
- context surrounding the event
- careful explanation of what is known and unknown

STRICT RULES:

- Never invent facts.
- Never invent dialogue.
- Never invent witnesses.
- Never invent evidence.
- Never invent events.
- Never present speculation as fact.
- Do not repeat paragraphs.
- Do not use filler.
- Keep the narration natural.
- Keep the tone serious and investigative.
- Do not add headings.
- Do not add bullet points.
- Do not add timestamps.
- Do not add production notes.

Return ONLY the complete expanded Turkish narration.
"""

    expanded = call_gemini(
        client,
        prompt
    )

    return expanded


def main():

    print(
        "SHADOW ARCHIVE — LONG SCRIPT GENERATOR"
    )

    print("=" * 60)

    topic_data = load_topic()

    topic = topic_data["topic"]

    print("GÜNCEL KONU:")
    print(topic)
    print()

    report_file = find_latest_report()

    print("ARAŞTIRMA RAPORU:")
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

    script = generate_initial_script(
        client,
        topic_data,
        report
    )

    word_count = len(
        script.split()
    )

    print()
    print(
        f"İlk senaryo kelime sayısı: "
        f"{word_count}"
    )

    if word_count < MIN_WORDS:

        script = expand_script(
            client,
            script,
            topic,
            report,
            word_count
        )

        word_count = len(
            script.split()
        )

        print()
        print(
            f"Genişletilmiş senaryo kelime sayısı: "
            f"{word_count}"
        )

    if word_count < MIN_WORDS:

        raise RuntimeError(
            "Senaryo hâlâ 2700 kelimenin altında: "
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

    print("=" * 60)


if __name__ == "__main__":
    main()
