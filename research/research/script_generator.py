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

Write a long-form ORIGINAL Turkish documentary narration
about the MV Joyita mystery.

TARGET LENGTH:
2,200–2,800 Turkish words.

The narration should be approximately 15–20 minutes long.

IMPORTANT:
- Never invent facts.
- Never invent dialogue.
- Never invent witnesses.
- Never invent evidence.
- Never invent events.
- Never present rumors as facts.
- Separate confirmed facts from theories.
- Do not repeat information just to make the script longer.
- Expand important factual details naturally.
- Explain the timeline carefully.
- Explain the investigation and evidence.
- Examine the major theories.
- Explain why theories are supported or weakened.
- Clearly explain what remains unknown.

STYLE:
- Natural Turkish.
- Serious documentary narration.
- Varied sentence lengths.
- Natural transitions.
- Strong opening.
- Gradually increasing suspense.
- Avoid repetitive AI-style phrases.
- Do not use excessive clickbait.

STRUCTURE:

OPENING HOOK

THE BACKGROUND

THE VOYAGE

THE DISCOVERY

THE INVESTIGATION

THE MISSING PEOPLE

THE MAIN THEORIES

WHAT THE OFFICIAL INVESTIGATION FOUND

WHAT WE STILL DON'T KNOW

FINAL

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

    if word_count < 1800:
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

    print("SENARYO BAŞARIYLA KAYDEDİLDİ")
    print(f"Dosya: {script_file}")


if __name__ == "__main__":
    main()
