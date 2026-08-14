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
You are the documentary scriptwriter for the YouTube channel
"Shadow Archive".

Use the following factual research report:

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

Write an ORIGINAL Turkish documentary narration.

Requirements:

- Target length: 15–20 minutes.
- Natural, human-sounding Turkish.
- Strong cinematic opening.
- Build suspense gradually.
- Tell the story chronologically.
- Keep confirmed facts separate from theories.
- Never present speculation as fact.
- Never invent dialogue.
- Never invent evidence.
- Never invent witnesses or events.
- Do not exaggerate facts.
- Do not use generic AI-style phrases repeatedly.
- Make the narration feel like a serious documentary.
- Explain important details naturally.
- End with the strongest unanswered question.

Structure:

1. OPENING HOOK
2. THE BACKGROUND
3. WHAT HAPPENED
4. THE DISCOVERY
5. THE INVESTIGATION
6. THE MAIN THEORIES
7. WHAT WE ACTUALLY KNOW
8. WHAT REMAINS UNEXPLAINED
9. FINAL

Write ONLY the narration.

Do not include:
- camera directions
- scene directions
- sound effects
- editing instructions
- timestamps
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

    report = json.loads(
        REPORT_FILE.read_text(
            encoding="utf-8"
        )
    )

    print("SHADOW ARCHIVE — SCRIPT GENERATOR")
    print("=" * 50)

    print("Web araştırma raporu bulundu.")

    script = generate_script(report)

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

    print("Senaryo oluşturuldu.")
    print(f"Dosya: {script_file}")


if __name__ == "__main__":
    main()
