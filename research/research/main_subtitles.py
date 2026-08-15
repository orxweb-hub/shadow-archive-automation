import json
import os
import subprocess
from pathlib import Path

from google import genai


SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
AUDIO_FILE = Path("research/audio/mv_joyita_voice.wav")
OUTPUT_FILE = Path("research/video/subtitles/mv_joyita_english.srt")

MODEL = "gemini-3.6-flash"


def get_audio_duration():
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(AUDIO_FILE),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(result.stdout.strip())


def srt_time(seconds):

    milliseconds = int(
        round((seconds % 1) * 1000)
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


def clean_json(raw):

    raw = raw.strip()

    if raw.startswith("```"):
        raw = raw.replace(
            "```json",
            ""
        )

        raw = raw.replace(
            "```",
            ""
        )

    return raw.strip()


def main():

    print("=" * 60)
    print("SHADOW ARCHIVE — MAIN ENGLISH SUBTITLES V3")
    print("=" * 60)

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY bulunamadı."
        )

    if not SCRIPT_FILE.exists():
        raise FileNotFoundError(
            "Ana senaryo bulunamadı."
        )

    if not AUDIO_FILE.exists():
        raise FileNotFoundError(
            "Ana ses dosyası bulunamadı."
        )

    script = SCRIPT_FILE.read_text(
        encoding="utf-8"
    ).strip()

    duration = get_audio_duration()

    print(
        f"Gerçek ses süresi: "
        f"{duration / 60:.2f} dakika"
    )

    client = genai.Client(
        api_key=api_key
    )

    prompt = f"""
You are creating professional English subtitles
for a serious mystery documentary.

Translate the Turkish narration into natural,
clear American English.

IMPORTANT:

- Translate the COMPLETE narration.
- Do NOT summarize.
- Do NOT remove information.
- Do NOT add information.
- Do NOT invent dialogue.
- Preserve factual meaning.
- Keep the documentary tone.
- Use short subtitle sentences.
- Each subtitle should normally contain
  5 to 12 words.
- Avoid long paragraphs.
- Keep sentences natural for subtitles.
- Do not use timestamps.
- Return ONLY valid JSON.

JSON FORMAT:

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

    print(
        "İngilizce altyazı oluşturuluyor..."
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    raw = clean_json(
        response.text
    )

    data = json.loads(raw)

    subtitles = data.get(
        "subtitles",
        []
    )

    if not subtitles:
        raise RuntimeError(
            "Altyazı oluşturulamadı."
        )

    total_words = sum(
        len(
            item["text"].split()
        )
        for item in subtitles
    )

    if total_words <= 0:
        raise RuntimeError(
            "Altyazı metni boş."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = []

    current_time = 0.0

    for index, item in enumerate(
        subtitles,
        start=1
    ):

        text = (
            item["text"]
            .strip()
        )

        if not text:
            continue

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

        end = (
            current_time +
            subtitle_duration
        )

        # Çok kısa altyazıları okunabilir
        # minimum süreye çıkar.
        if subtitle_duration < 0.9:
            end = start + 0.9

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
    print("=" * 60)
    print("İNGİLİZCE ALTYAZI HAZIR")
    print("=" * 60)
    print(
        f"Dosya: {OUTPUT_FILE}"
    )
    print(
        f"Altyazı sayısı: {len(output)}"
    )


if __name__ == "__main__":
    main()
