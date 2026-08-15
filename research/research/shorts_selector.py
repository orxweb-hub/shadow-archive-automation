import json
import os
from pathlib import Path

from google import genai

SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
OUTPUT_FILE = Path("research/video/shorts_selection.json")

MODEL = "gemini-3.6-flash"


def main():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    if not SCRIPT_FILE.exists():
        raise FileNotFoundError(
            f"Script bulunamadı: {SCRIPT_FILE}"
        )

    script = SCRIPT_FILE.read_text(
        encoding="utf-8"
    )

    client = genai.Client(
        api_key=api_key
    )

    prompt = f"""
You are selecting two YouTube Shorts from a serious
documentary script.

MAIN SCRIPT:
{script}

Create EXACTLY 2 Shorts.

Rules for each Short:
- 30–60 seconds when narrated naturally
- Strong first sentence / hook
- Based ONLY on facts in the script
- No invented facts
- No fake dialogue
- No exaggerated false claims
- Must create curiosity
- Must end with an unresolved question, mystery,
  or reason to continue watching
- Turkish narration
- Natural spoken Turkish
- Suitable for Shadow Archive
- Serious documentary tone

Also create an English subtitle version of the
EXACT SAME narration.

The English version must:
- Preserve the meaning
- Sound natural to a native English speaker
- Not be a literal word-for-word translation
- Contain no extra facts

Return ONLY valid JSON in this exact structure:

{{
  "shorts": [
    {{
      "short": 1,
      "title": "Turkish title",
      "narration": "Turkish narration",
      "english_script": "Natural English subtitle text"
    }},
    {{
      "short": 2,
      "title": "Turkish title",
      "narration": "Turkish narration",
      "english_script": "Natural English subtitle text"
    }}
  ]
}}
"""

    print("Gemini Shorts seçimini yapıyor...")

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    data = json.loads(text)

    if "shorts" not in data:
        raise ValueError(
            "Gemini çıktısında 'shorts' bulunamadı."
        )

    if len(data["shorts"]) != 2:
        raise ValueError(
            "Tam olarak 2 Shorts üretilmeliydi."
        )

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

    print()
    print("2 Shorts başarıyla hazırlandı.")
    print()
    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()
