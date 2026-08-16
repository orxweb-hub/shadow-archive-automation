import json
import os
import re
from pathlib import Path

from google import genai


TOPIC_FILE = Path("research/current_topic.json")
SCRIPT_DIR = Path("research/scripts")
OUTPUT_DIR = Path("research/video")

MODEL = "gemini-3.6-flash"


def create_safe_filename(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")

    if not text:
        text = "daily_topic"

    return text[:80]


def load_current_topic():
    if not TOPIC_FILE.exists():
        raise FileNotFoundError(
            f"current_topic.json bulunamadı: {TOPIC_FILE}"
        )

    data = json.loads(
        TOPIC_FILE.read_text(
            encoding="utf-8"
        )
    )

    topic = data.get("topic")

    if not topic:
        raise RuntimeError(
            "current_topic.json içinde topic bulunamadı."
        )

    return data


def find_script(topic):
    safe_name = create_safe_filename(topic)

    expected_file = (
        SCRIPT_DIR /
        f"{safe_name}_script.txt"
    )

    if expected_file.exists():
        return expected_file

    scripts = sorted(
        SCRIPT_DIR.glob("*_script.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if scripts:
        return scripts[0]

    raise FileNotFoundError(
        "Hiçbir script bulunamadı."
    )


def generate_shorts(client, topic_data, script):
    topic = topic_data["topic"]
    category = topic_data.get("category", "Mystery")

    prompt = f"""
You are the Shorts editor for Shadow Archive,
a serious Turkish documentary YouTube channel.

TOPIC:
{topic}

CATEGORY:
{category}

MAIN DOCUMENTARY SCRIPT:
{script}

Create EXACTLY 2 YouTube Shorts from this documentary.

IMPORTANT:
Both Shorts MUST use only information contained
in the documentary script.

Do not invent:
- facts
- dates
- names
- dialogue
- locations
- quotes
- theories presented as facts

SHORT #1 — 09:00 TEASER

Purpose:
Create curiosity before the main documentary.

Rules:
- 30–60 seconds when narrated naturally
- Very strong opening hook
- Introduce the central mystery
- Reveal enough information to create curiosity
- Do NOT reveal the entire story
- End with a question or unresolved mystery
- Make viewers want to watch the main video

SHORT #2 — 21:00 HIGHLIGHT

Purpose:
Create a second wave of traffic after the main video.

Rules:
- 30–60 seconds when narrated naturally
- Use one of the strongest moments from the documentary
- Strong opening sentence
- Give viewers a surprising or important detail
- End with an unresolved question or mystery
- Encourage curiosity about the full documentary

STYLE:
- Turkish
- Natural spoken Turkish
- Serious documentary tone
- Cinematic
- Human-sounding
- No exaggerated clickbait
- No fake suspense
- No emojis inside narration

For each Short also create an English subtitle
version of the EXACT SAME narration.

English subtitle rules:
- Preserve the meaning
- Natural English
- Not word-for-word translation
- No extra information
- No invented facts

Return ONLY valid JSON.

EXACT STRUCTURE:

{{
  "shorts": [
    {{
      "short": 1,
      "schedule": "09:00",
      "purpose": "teaser",
      "title": "Turkish title",
      "narration": "Turkish narration",
      "english_script": "Natural English subtitle text"
    }},
    {{
      "short": 2,
      "schedule": "21:00",
      "purpose": "highlight",
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

    for index, short in enumerate(
        data["shorts"],
        start=1
    ):
        required_fields = [
            "short",
            "schedule",
            "purpose",
            "title",
            "narration",
            "english_script"
        ]

        for field in required_fields:
            if field not in short:
                raise ValueError(
                    f"Short #{index} içinde "
                    f"'{field}' bulunamadı."
                )

        narration_words = len(
            short["narration"].split()
        )

        if narration_words < 50:
            raise ValueError(
                f"Short #{index} çok kısa: "
                f"{narration_words} kelime."
            )

        if narration_words > 180:
            raise ValueError(
                f"Short #{index} çok uzun: "
                f"{narration_words} kelime."
            )

    return data


def main():
    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY bulunamadı."
        )

    topic_data = load_current_topic()

    topic = topic_data["topic"]

    script_file = find_script(topic)

    print(
        f"Script bulundu: {script_file}"
    )

    script = script_file.read_text(
        encoding="utf-8"
    )

    client = genai.Client(
        api_key=api_key
    )

    data = generate_shorts(
        client,
        topic_data,
        script
    )

    safe_name = create_safe_filename(
        topic
    )

    output_file = (
        OUTPUT_DIR /
        f"{safe_name}_shorts_selection.json"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("==========================================")
    print("2 SHORTS BAŞARIYLA HAZIRLANDI")
    print("==========================================")

    for short in data["shorts"]:
        print(
            f"Short #{short['short']} "
            f"| {short['schedule']} "
            f"| {short['purpose']}"
        )
        print(
            f"Başlık: {short['title']}"
        )
        print()

    print(
        f"Dosya: {output_file}"
    )


if __name__ == "__main__":
    main()
