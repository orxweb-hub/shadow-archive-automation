import os
import json
from pathlib import Path

from google import genai


REPORT_FILE = Path("research/reports/mv_joyita_web_research.json")
SCRIPT_DIR = Path("research/scripts")

MIN_WORDS = 2700


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    return genai.Client(api_key=api_key)


def generate_initial_script(client, report):

    prompt = f"""
You are the senior documentary writer for the YouTube channel
"Shadow Archive".

Write a professional, original Turkish documentary narration
about the MV Joyita mystery.

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

TARGET:
2,700–3,200 Turkish words.

The final narration should be approximately 15–20 minutes long.

FACTUAL RULES:
- Use only information supported by the research report.
- Never invent facts.
- Never invent dialogue.
- Never invent witnesses.
- Never invent evidence.
- Never invent events.
- Never present rumors as facts.
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

Write ONLY the narration.

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
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text.strip()


def expand_script(client, script, report):

    prompt = f"""
You are editing a professional Turkish documentary narration
for the YouTube channel "Shadow Archive".

CURRENT SCRIPT:
{script}

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

The current script is too short.

Expand it naturally to at least 2,700 words.

IMPORTANT:
- Do NOT rewrite the entire story from scratch.
- Preserve the existing factual information.
- Add useful factual context and explanation.
- Expand the timeline.
- Expand the investigation.
- Explain the evidence more carefully.
- Examine the theories more deeply.
- Explain why some theories are weak or uncertain.
- Add context only when supported by the research report.
- Do not invent anything.
- Do not repeat paragraphs.
- Do not use filler.
- Do not add fake dialogue.
- Do not add fictional scenes.

The final result must be a single continuous Turkish narration.

Write ONLY the finished narration.
Do not include headings, bullet points, timestamps,
camera directions, sound effects, or production notes.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text.strip()


def main():

    print("SHADOW ARCHIVE — AUTOMATIC LONG SCRIPT GENERATOR")
    print("=" * 60)

    if not REPORT_FILE.exists():
        raise FileNotFoundError(
            f"Web araştırma raporu bulunamadı: {REPORT_FILE}"
        )

    report = json.loads(
        REPORT_FILE.read_text(encoding="utf-8")
    )

    client = get_client()

    print("İlk uzun senaryo oluşturuluyor...")

    script = generate_initial_script(
        client,
        report
    )

    word_count = len(script.split())

    print(f"İlk kelime sayısı: {word_count}")

    # Kısa kaldıysa otomatik genişlet
    attempts = 0

    while word_count < MIN_WORDS and attempts < 2:

        attempts += 1

        print()
        print(
            f"Senaryo kısa. Otomatik genişletme başlıyor..."
        )
        print(
            f"Deneme: {attempts}/2"
        )

        script = expand_script(
            client,
            script,
            report
        )

        word_count = len(script.split())

        print(
            f"Yeni kelime sayısı: {word_count}"
        )

    if word_count < 1800:
        raise RuntimeError(
            f"Senaryo çok kısa kaldı: {word_count} kelime."
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
    print("SENARYO BAŞARIYLA HAZIRLANDI")
    print("=" * 60)
    print(f"Kelime sayısı: {word_count}")
    print(f"Dosya: {script_file}")


if __name__ == "__main__":
    main()
