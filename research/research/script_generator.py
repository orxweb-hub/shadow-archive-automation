import os
import json
from pathlib import Path
from google import genai

REPORT_FILE = Path("research/reports/mv_joyita.json")
SCRIPT_DIR = Path("research/scripts")


def generate_script(report):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the documentary scriptwriter for the YouTube channel
"Shadow Archive".

Use ONLY the research report below.

RESEARCH REPORT:
{json.dumps(report, ensure_ascii=False, indent=2)}

Write an ORIGINAL Turkish documentary script about this case.

Requirements:
- Target length: 15–20 minutes.
- Natural Turkish narration.
- Do not sound like an AI or a school essay.
- Start with a strong cinematic hook.
- Build suspense gradually.
- Tell the story chronologically.
- Clearly distinguish confirmed facts from theories.
- Never present speculation as fact.
- Do not invent dialogue, evidence, witnesses or events.
- Explain important details naturally.
- Include transitions between sections.
- End with the strongest unanswered question.
- Do not use clickbait claims that the evidence cannot support.

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

Write only the narration.
Do not include camera directions, sound effects or editing instructions.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text.strip()


def main():
    if not REPORT_FILE.exists():
        raise FileNotFoundError(
            f"Araştırma raporu bulunamadı: {REPORT_FILE}"
        )

    report = json.loads(
        REPORT_FILE.read_text(encoding="utf-8")
    )

    script = generate_script(report)

    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    script_file = SCRIPT_DIR / "mv_joyita_script.txt"

    script_file.write_text(
        script,
        encoding="utf-8"
    )

    print("SHADOW ARCHIVE — SCRIPT GENERATED")
    print("=" * 45)
    print(f"Senaryo kaydedildi: {script_file}")
    print()
    print(script)


if __name__ == "__main__":
    main()
