import os
import json
from pathlib import Path

from google import genai


REPORT_FILE = Path("research/reports/mv_joyita_web_research.json")
SCRIPT_DIR = Path("research/scripts")

MIN_WORDS = 2700
MAX_WORDS = 3200
MODEL = "gemini-3.6-flash"


def get_client():

    api_key = os.environ.get("GEMINI_API_KEY")

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
- Clear and human-sounding narration.
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

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    if not text:
        raise RuntimeError(
            "Gemini boş bir senaryo döndürdü."
        )

    return text


def main():

    print(
        "SHADOW ARCHIVE — LONG SCRIPT GENERATOR"
    )

    print("=" * 60)

    if not REPORT_FILE.exists():

        raise FileNotFoundError(
            f"Web araştırma raporu bulunamadı: "
            f"{REPORT_FILE}"
        )

    report = json.loads(
        REPORT_FILE.read_text(
            encoding="utf-8"
        )
    )

    client = get_client()

    print(
        "Gemini ile tek seferlik uzun "
        "senaryo oluşturuluyor..."
    )

    script = generate_script(
        client,
        report
    )

    word_count = len(
        script.split()
    )

    print(
        f"Senaryo kelime sayısı: "
        f"{word_count}"
    )

    if word_count < 1800:

        raise RuntimeError(
            f"Senaryo çok kısa kaldı: "
            f"{word_count} kelime. "
            f"İkinci Gemini isteği yapılmadı; "
            f"günlük kota korunuyor."
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
        "Gemini isteği: 1"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
