import os
import json
from pathlib import Path

from google import genai

SELECTION_FILE = Path("research/video/shorts_selection.json")
OUTPUT_DIR = Path("research/video/subtitles")


def main():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    if not SELECTION_FILE.exists():
        raise FileNotFoundError(
            "Shorts seçim dosyası bulunamadı."
        )

    data = json.loads(
        SELECTION_FILE.read_text(
            encoding="utf-8"
        )
    )

    client = genai.Client(
        api_key=api_key
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for short in data["shorts"]:

        number = short["short"]
        script = short["script"]

        prompt = f"""
You are a professional English subtitle writer.

Translate the following Turkish YouTube Shorts narration
into natural, concise English.

IMPORTANT:
- Preserve the exact meaning.
- Do not add information.
- Do not remove important information.
- Do not translate word-for-word if it sounds unnatural.
- Make it sound like a professional documentary.
- Keep sentences short enough for subtitles.

TURKISH SCRIPT:

{script}

Return ONLY the English translation.
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        english = response.text.strip()

        output_file = (
            OUTPUT_DIR /
            f"short_{number}_english.txt"
        )

        output_file.write_text(
            english,
            encoding="utf-8"
        )

        print(
            f"Short {number} English subtitle hazır."
        )

    print("=" * 60)
    print("ENGLISH SUBTITLE GENERATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
