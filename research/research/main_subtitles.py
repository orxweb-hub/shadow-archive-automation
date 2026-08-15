import json
import os
from pathlib import Path

from google import genai


SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
OUTPUT_FILE = Path("research/video/subtitles/mv_joyita_english.srt")

MODEL = "gemini-3.6-flash"


def main():
    print("=" * 60)
    print("SHADOW ARCHIVE — MAIN VIDEO ENGLISH SUBTITLES")
    print("=" * 60)

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    if not SCRIPT_FILE.exists():
        raise FileNotFoundError(
            "mv_joyita_script.txt bulunamadı."
        )

    script = SCRIPT_FILE.read_text(
        encoding="utf-8"
    ).strip()

    client = genai.Client(
        api_key=api_key
    )

    prompt = f"""
You are creating professional English subtitles for a
serious mystery documentary.

Translate the Turkish narration below into natural,
clear American English.

IMPORTANT:
- Do NOT summarize.
- Do NOT remove information.
- Preserve the meaning and factual details.
- Keep the tone serious and cinematic.
- Break the narration into short subtitle sentences.
- Each subtitle should contain approximately 5–12 words.
- Avoid huge blocks of text.
- Do not use quotation marks unless they exist in the narration.
- Do not add facts.
- Do not invent dialogue.
- Return ONLY valid JSON.

JSON format:

{{
  "subtitles": [
    {{
      "text": "English subtitle sentence"
    }}
  ]
}}

TURKISH NARRATION:

{script}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

    data = json.loads(raw)

    subtitles = data.get("subtitles", [])

    if not subtitles:
        raise RuntimeError(
            "İngilizce altyazı oluşturulamadı."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = []

    # Yaklaşık zamanlama.
    # Daha sonra gerçek ses süresine göre
    # otomatik olarak ayarlanacak.
    total_words = sum(
        len(item["text"].split())
        for item in subtitles
    )

    duration = 1753.36

    current_time = 0.0

    for index, item in enumerate(subtitles, start=1):

        text = item["text"].strip()

        word_count = max(
            len(text.split()),
            1
        )

        subtitle_duration = (
            duration *
            word_count /
            total_words
        )

        start = current_time
        end = current_time + subtitle_duration

        # Çok uzun altyazıları biraz sınırla
        if subtitle_duration < 1.0:
            end = start + 1.0

        def srt_time(seconds):

            milliseconds = int(
                (seconds % 1) * 1000
            )

            total_seconds = int(seconds)

            hours = total_seconds // 3600
            minutes = (
                total_seconds % 3600
            ) // 60

            secs = total_seconds % 60

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d},"
                f"{milliseconds:03d}"
            )

        output.append(
            f"{index}\n"
            f"{srt_time(start)} --> "
            f"{srt_time(end)}\n"
            f"{text}\n"
        )

        current_time = end

    OUTPUT_FILE.write_text(
        "\n".join(output),
        encoding="utf-8"
    )

    print()
    print("İNGİLİZCE ALTYAZI HAZIR!")
    print(
        f"Dosya: {OUTPUT_FILE}"
    )
    print(
        f"Toplam altyazı: {len(subtitles)}"
    )


if __name__ == "__main__":
    main()
