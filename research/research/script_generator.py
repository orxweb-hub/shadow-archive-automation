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
TARGET_WORDS = 3000

PRIMARY_MODEL = "gemini-3.6-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

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
            f"Güncel konu dosyası bulunamadı: {TOPIC_FILE}"
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


def is_quota_error(error):

    error_text = str(error).lower()

    return (
        "429" in error_text
        or
        "resource_exhausted" in error_text
        or
        "quota" in error_text
        or
        "rate limit" in error_text
    )


def is_temporary_error(error):

    error_text = str(error).lower()

    return (
        "503" in error_text
        or
        "unavailable" in error_text
        or
        "high demand" in error_text
        or
        "500" in error_text
        or
        "internal" in error_text
    )


def call_model(
    client,
    prompt,
    model
):

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print()
            print(
                f"MODEL: {model}"
            )

            print(
                f"Gemini isteği "
                f"{attempt}/{MAX_RETRIES}"
            )

            response = client.models.generate_content(
                model=model,
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
                f"Gemini üretimi başarılı: {model}"
            )

            return text

        except Exception as error:

            print()
            print("Gemini hatası:")
            print(error)

            if is_quota_error(error):

                print(
                    f"{model} kota/rate limit nedeniyle "
                    "kullanılamıyor."
                )

                raise error

            if is_temporary_error(error):

                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        f"{model} geçici hata nedeniyle "
                        "başarısız oldu."
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
                    f"{model} ile üretim başarısız oldu."
                ) from error

            delay = RETRY_DELAYS[
                attempt - 1
            ]

            print(
                f"{delay} saniye bekleniyor..."
            )

            time.sleep(delay)

    raise RuntimeError(
        f"{model} cevap üretemedi."
    )


def generate_with_fallback(
    client,
    prompt
):

    try:

        print()
        print(
            "1. ÖNCELİKLİ MODEL:"
        )

        print(
            PRIMARY_MODEL
        )

        return call_model(
            client,
            prompt,
            PRIMARY_MODEL
        )

    except Exception as primary_error:

        if not is_quota_error(
            primary_error
        ):
            raise

        print()
        print(
            "⚠️ 3.6 Flash kota/rate limit."
        )

        print(
            "🔄 Otomatik olarak "
            "3.5 Flash Lite'a geçiliyor..."
        )

        print(
            FALLBACK_MODEL
        )

        return call_model(
            client,
            prompt,
            FALLBACK_MODEL
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

Write approximately 3,000 Turkish words.

The final narration MUST contain at least 2,700 words.

Aim for 2,900–3,200 words.

Do not stop early.

Do not produce a short summary.

Develop the story fully from beginning to end.

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
- Official investigation.
- Official findings.
- Major theories.
- Problems and contradictions.
- What remains unexplained.
- Strong final conclusion.

IMPORTANT:

Do not finish the narration before reaching the required length.

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

    return generate_with_fallback(
        client,
        prompt
    )


def generate_additional_section(
    client,
    topic,
    report,
    current_script,
    current_words
):

    missing_words = MIN_WORDS - current_words

    if missing_words <= 0:
        return ""

    # Modelden eksikten daha fazla kelime istiyoruz.
    # Böylece 2700 sınırını rahat geçmesi hedefleniyor.
    requested_words = max(
        missing_words + 350,
        500
    )

    prompt = f"""
You are a senior investigative documentary writer
for the YouTube channel "Shadow Archive".

We already have a finished Turkish documentary narration.

IMPORTANT:
DO NOT rewrite the existing narration.

DO NOT summarize the existing narration.

DO NOT return the existing narration.

Your ONLY task is to write a NEW ADDITIONAL SECTION
that can be appended to the END of the existing narration.

TOPIC:
{topic}

CURRENT WORD COUNT:
{current_words}

MINIMUM FINAL WORD COUNT:
{MIN_WORDS}

WORDS CURRENTLY MISSING:
{missing_words}

WRITE AT LEAST:
{requested_words} Turkish words.

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

CURRENT NARRATION:
{current_script}

The additional section should naturally continue the story.

Use factual material that has not already been sufficiently
developed in the current narration.

Good areas include:

- additional chronology
- investigation details
- evidence
- people involved
- locations
- official findings
- competing theories
- contradictions
- unanswered questions
- historical context
- consequences
- final analysis

STRICT RULES:

- Do not invent facts.
- Do not invent dialogue.
- Do not invent witnesses.
- Do not invent evidence.
- Do not invent events.
- Do not present theories as facts.
- Do not repeat the current narration.
- Do not copy existing paragraphs.
- Do not use filler.
- Do not use a generic conclusion unless it adds useful information.
- Continue naturally from the existing story.

VERY IMPORTANT:

The output will be directly appended to the existing narration.

Therefore begin naturally as a continuation of the documentary.

Do NOT write an introduction such as:
"Tabii, işte..."
"Elbette..."
"Bu bölümde..."
"Sonuç olarak..."

Write ONLY the NEW ADDITIONAL SECTION.

Do not include:

- headings
- bullet points
- timestamps
- camera directions
- sound effects
- editing instructions
- production notes
"""

    return generate_with_fallback(
        client,
        prompt
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

    print()
    print(
        "Uzun Türkçe senaryo oluşturuluyor..."
    )

    print(
        f"Öncelik: {PRIMARY_MODEL}"
    )

    print(
        f"Otomatik yedek: {FALLBACK_MODEL}"
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

    MAX_EXPANSION_ROUNDS = 6

    expansion_round = 0

    while (
        word_count < MIN_WORDS
        and
        expansion_round < MAX_EXPANSION_ROUNDS
    ):

        expansion_round += 1

        print()
        print(
            "=========================================="
        )

        print(
            f"EK BÖLÜM ÜRETİMİ "
            f"{expansion_round}/{MAX_EXPANSION_ROUNDS}"
        )

        print(
            "=========================================="
        )

        missing = MIN_WORDS - word_count

        print(
            f"Mevcut kelime: {word_count}"
        )

        print(
            f"Eksik kelime: {missing}"
        )

        additional_section = generate_additional_section(
            client,
            topic,
            report,
            script,
            word_count
        )

        additional_words = len(
            additional_section.split()
        )

        print()
        print(
            f"Üretilen ek bölüm: "
            f"{additional_words} kelime"
        )

        # Ek bölüm gerçekten içerik ürettiyse
        # mevcut senaryonun SONUNA ekliyoruz.
        if additional_words > 0:

            script = (
                script.rstrip()
                + "\n\n"
                + additional_section.strip()
            )

            word_count = len(
                script.split()
            )

            print(
                f"Yeni toplam kelime sayısı: "
                f"{word_count}"
            )

        else:

            print(
                "⚠️ Ek bölüm boş geldi."
            )

            print(
                "Bir sonraki tur denenecek."
            )

        if word_count >= MIN_WORDS:

            print()
            print(
                "✅ 2700 kelime sınırı aşıldı."
            )

            break

    if word_count < MIN_WORDS:

        raise RuntimeError(
            "Ek bölüm üretimlerinden sonra "
            "senaryo 2700 kelimeye ulaşamadı: "
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
        SCRIPT_DIR
        / f"{safe_name}_script.txt"
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
        "3.6 Flash → kota varsa → "
        "3.5 Flash Lite otomatik geçiş aktif."
    )

    print(
        "Eksik kelimeler artık mevcut senaryonun "
        "sonuna ek bölüm olarak tamamlanıyor."
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
