import os
import json
import time
from pathlib import Path

from google import genai


REPORT_FILE = Path(
    "research/reports/mv_joyita_web_research.json"
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


def generate_script(client, report):

    prompt = f"""
You are the senior documentary writer for the YouTube channel
"Shadow Archive".

Write a professional, original Turkish documentary narration
about the MV Joyita mystery.

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

TARGET LENGTH:
2,700–3,200 Turkish words.

IMPORTANT:
The narration MUST aim for at least 2,700 words in a SINGLE
generation. Do not intentionally make it short.

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

- The background of MV Joyita.
- The voyage.
- The disappearance.
- The discovery of the abandoned vessel.
- The missing people.
- The physical evidence.
- The investigation.
- The official findings.
- The major theories.
- Problems with each theory.
- What remains unexplained.
- A strong final conclusion.

STRUCTURE:

1. Strong opening and mystery
2. Background of the vessel
3. Events before the disappearance
4. The disappearance
5. Discovery of MV Joyita
6. Evidence found aboard
7. Missing people
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
                f"Gemini senaryo üretimi "
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

                print()
                print(
                    f"Gemini yoğun. "
                    f"{delay} saniye bekleniyor..."
                )

                time.sleep(delay)

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

            time.sleep(delay)

    raise RuntimeError(
        "Gemini senaryo üretilemedi."
    )


def main():

    print(
        "SHADOW ARCHIVE — LONG SCRIPT GENERATOR"
    )

    print("=" * 60)

    if not REPORT_FILE.exists():

        raise FileNotFoundError(
            "Web araştırma raporu bulunamadı: "
            f"{REPORT_FILE}"
        )

    report = json.loads(
        REPORT_FILE.read_text(
            encoding="utf-8"
        )
    )

    client = get_client()

    print(
        "Uzun Türkçe senaryo oluşturuluyor..."
    )

    script = generate_script(
        client,
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

    if word_count < 1800:

        raise RuntimeError(
            f"Senaryo çok kısa kaldı: "
            f"{word_count} kelime."
        )

    SCRIPT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    script_file = (
        SCRIPT_DIR /
        "mv_joyita_script.txt"
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
