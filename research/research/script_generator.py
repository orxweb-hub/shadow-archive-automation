import os
import json
from pathlib import Path

from google import genai


REPORT_FILE = Path("research/reports/mv_joyita_web_research.json")
SCRIPT_DIR = Path("research/scripts")


def generate_script(report):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the senior documentary writer for the YouTube channel
"Shadow Archive".

Use ONLY the factual research report below.

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

Write a LONG-FORM ORIGINAL Turkish documentary narration
about the MV Joyita mystery.

TARGET LENGTH:
2,500–3,000 Turkish words.

The narration should be approximately 15–20 minutes long.

IMPORTANT FACTUAL RULES:
- Never invent facts.
- Never invent dialogue.
- Never invent witnesses.
- Never invent evidence.
- Never invent events.
- Never present rumors as confirmed facts.
- Clearly separate confirmed facts from theories.
- If information is uncertain, say that it is uncertain.
- Do not repeat the same information simply to increase length.
- Expand important factual details with explanation and context.
- Explain the timeline carefully.
- Explain what happened before the disappearance.
- Explain the voyage and circumstances surrounding the disappearance.
- Explain how the vessel was discovered.
- Explain the investigation.
- Examine the evidence carefully.
- Examine the major theories.
- Explain why each theory is considered possible or unlikely.
- Explain what the official investigation concluded.
- Clearly explain what remains unknown.

STYLE:
- Natural Turkish.
- Serious investigative documentary style.
- Human-like narration.
- Varied sentence lengths.
- Natural transitions.
- Strong opening.
- Gradually increasing suspense.
- Avoid repetitive AI-style phrases.
- Avoid excessive clickbait.
- Do not constantly use phrases such as
  "düşünün", "asıl soru şu", "işte burada".
- Do not use filler sentences.
- Every paragraph should add useful information.
- Make the narration feel like a professional documentary.

STRUCTURE:

OPENING HOOK

THE BACKGROUND

THE VOYAGE

THE DISCOVERY

THE INVESTIGATION

THE MISSING PEOPLE

THE EVIDENCE

THE MAIN THEORIES

WHAT THE OFFICIAL INVESTIGATION FOUND

WHAT THE THEORIES CANNOT EXPLAIN

WHAT WE STILL DON'T KNOW

FINAL

IMPORTANT:
Write enough detail to reach 2,500–3,000 words.
Do not stop early.

Write ONLY the narration.

Do not include:
- headings
- bullet points
- camera directions
- sound effects
- editing instructions
- timestamps
- production notes
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text.strip()


def main():

    if not REPORT_FILE.exists():
        raise FileNotFoundError(
            f"Web araştırma raporu bulunamadı: {REPORT_FILE}"
        )

    print("SHADOW ARCHIVE — LONG SCRIPT GENERATOR")
    print("=" * 55)

    report = json.loads(
        REPORT_FILE.read_text(
            encoding="utf-8"
        )
    )

    script = generate_script(report)

    word_count = len(script.split())

    print(f"Üretilen kelime sayısı: {word_count}")

    if word_count < 1500:
        raise RuntimeError(
            f"Senaryo çok kısa: {word_count} kelime."
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
    print("SENARYO BAŞARIYLA KAYDEDİLDİ")
    print("=" * 55)
    print(f"Dosya: {script_file}")
    print(f"Kelime sayısı: {word_count}")


if __name__ == "__main__":
    main()
