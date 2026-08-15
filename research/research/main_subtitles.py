import json
import os
import re
import subprocess
import time
from pathlib import Path

from google import genai


SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
AUDIO_FILE = Path("research/audio/mv_joyita_voice.wav")
OUTPUT_FILE = Path(
    "research/video/subtitles/mv_joyita_english.srt"
)

MODEL = "gemini-3.6-flash"

# Metni yaklaşık bu büyüklükte parçalara ayırıyoruz.
CHUNK_SIZE = 7000


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


def clean_json(text):

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?",
            "",
            text
        )

        text = re.sub(
            r"```$",
            "",
            text
        )

    return text.strip()


def split_script(text):

    paragraphs = re.split(
        r"\n\s*\n",
        text
    )

    chunks = []
    current = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if (
            len(current) +
            len(paragraph) +
            2
            <= CHUNK_SIZE
        ):
            current += (
                ("\n\n" if current else "")
                + paragraph
            )

        else:

            if current:
                chunks.append(current)

            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def translate_chunk(client, chunk, chunk_number):

    print(
        f"Altyazı parçası {chunk_number} "
        f"çevriliyor..."
    )

    prompt = f"""
You are translating part {chunk_number}
of a serious mystery documentary.

Translate the COMPLETE Turkish text below
into natural American English subtitles.

RULES:

- Translate everything.
- Do not summarize.
- Do not remove information.
- Do not add facts.
- Do not invent dialogue.
- Preserve the exact meaning.
- Keep the tone serious and cinematic.
- Break the text into short subtitle sentences.
- Prefer 5–12 words per subtitle.
- Each subtitle should normally be one sentence.
- Avoid huge text blocks.
- Do not include timestamps.
- Return ONLY valid JSON.

FORMAT:

{{
  "subtitles": [
    {{
      "text": "English subtitle"
    }}
  ]
}}

TURKISH TEXT:

{chunk}
"""

    for attempt in range(3):

        try:

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

            if subtitles:
                print(
                    f"Parça {chunk_number} hazır."
                )

                return subtitles

        except Exception as error:

            print(
                f"Deneme {attempt + 1} başarısız:"
            )

            print(error)

            if attempt < 2:
                print(
                    "10 saniye bekleniyor..."
                )

                time.sleep(10)

    raise RuntimeError(
        f"Parça {chunk_number} "
        "çevrilemedi."
    )


def main():

    print("=" * 65)
    print(
        "SHADOW ARCHIVE — "
        "MAIN SUBTITLES V3"
    )
    print("=" * 65)

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
        f"Ses süresi: "
        f"{duration / 60:.2f} dakika"
    )

    chunks = split_script(script)

    print(
        f"Toplam metin parçası: "
        f"{len(chunks)}"
    )

    client = genai.Client(
        api_key=api_key
    )

    all_subtitles = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        subtitles = translate_chunk(
            client,
            chunk,
            index
        )

        all_subtitles.extend(
            subtitles
        )

        # API'ye aşırı hızlı yüklenmemek için
        time.sleep(2)

    if not all_subtitles:
        raise RuntimeError(
            "Hiç altyazı oluşturulamadı."
        )

    total_words = sum(
        len(
            item["text"].split()
        )
        for item in all_subtitles
        if item.get("text")
    )

    if total_words <= 0:
        raise RuntimeError(
            "Altyazı kelime sayısı sıfır."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = []

    current_time = 0.0
    subtitle_number = 1

    for item in all_subtitles:

        text = item.get(
            "text",
            ""
        ).strip()

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

        # Çok kısa yazıları okunabilir tut.
        subtitle_duration = max(
            subtitle_duration,
            0.9
        )

        start = current_time

        end = min(
            current_time +
            subtitle_duration,
            duration
        )

        output.append(
            f"{subtitle_number}\n"
            f"{srt_time(start)} --> "
            f"{srt_time(end)}\n"
            f"{text}\n"
        )

        subtitle_number += 1
        current_time = end

        if current_time >= duration:
            break

    OUTPUT_FILE.write_text(
        "\n".join(output),
        encoding="utf-8"
    )

    print()
    print("=" * 65)
    print("İNGİLİZCE ALTYAZI TAMAMLANDI")
    print("=" * 65)
    print(
        f"Dosya: {OUTPUT_FILE}"
    )
    print(
        f"Toplam altyazı: "
        f"{len(output)}"
    )


if __name__ == "__main__":
    main()
