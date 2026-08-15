import os
import json
from pathlib import Path

from google import genai

SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
OUTPUT_FILE = Path("research/video/shorts_selection.json")


def main():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    if not SCRIPT_FILE.exists():
        raise FileNotFoundError("MV Joyita senaryosu bulunamadı.")

    script = SCRIPT_FILE.read_text(encoding="utf-8")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a professional YouTube Shorts editor.

Channel:
Shadow Archive

Topic:
MV Joyita

MAIN DOCUMENTARY SCRIPT:
{script}

Select exactly 2 sections that would work best as YouTube Shorts.

Each Short must:
- Be approximately 30–60 seconds when narrated.
- Start with a strong curiosity hook.
- Contain a surprising or mysterious fact.
- End with an unanswered question or curiosity gap.
- Be based ONLY on the script.
- Never invent facts.
- Never invent dialogue.
- Never exaggerate facts.
- Avoid repeating the same information in both Shorts.

Return ONLY valid JSON in this format:

{{
  "shorts": [
    {{
      "short": 1,
      "title": "",
      "hook": "",
      "script": "",
      "reason": ""
    }},
    {{
      "short": 2,
      "title": "",
      "hook": "",
      "script": "",
      "reason": ""
    }}
  ]
}}

The scripts should be natural Turkish narration.
Do not include timestamps.
Do not include camera directions.
Do not include editing instructions.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    data = json.loads(text)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("=" * 60)
    print("SHORTS SELECTION TAMAMLANDI")
    print("=" * 60)

    for short in data["shorts"]:
        print()
        print("SHORT:", short["short"])
        print("TITLE:", short["title"])
        print("HOOK:", short["hook"])
        print("SCRIPT:", short["script"][:300], "...")

    print()
    print(f"Dosya: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
