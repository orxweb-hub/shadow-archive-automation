import json
import re
from pathlib import Path


TOPIC_FILE = Path("research/current_topic.json")
SELECTION_DIR = Path("research/video")
OUTPUT_DIR = Path("research/video/subtitles")


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


def find_selection_file(topic):
    safe_name = create_safe_filename(topic)

    expected_file = (
        SELECTION_DIR /
        f"{safe_name}_shorts_selection.json"
    )

    if expected_file.exists():
        return expected_file

    fallback = (
        SELECTION_DIR /
        "shorts_selection.json"
    )

    if fallback.exists():
        return fallback

    files = sorted(
        SELECTION_DIR.glob(
            "*_shorts_selection.json"
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if files:
        return files[0]

    raise FileNotFoundError(
        "Shorts seçim dosyası bulunamadı."
    )


def main():

    print("=" * 60)
    print("SHADOW ARCHIVE — ENGLISH SUBTITLES")
    print("=" * 60)

    topic_data = load_current_topic()

    topic = topic_data["topic"]

    selection_file = find_selection_file(
        topic
    )

    print(
        f"Shorts seçimi: {selection_file}"
    )

    data = json.loads(
        selection_file.read_text(
            encoding="utf-8"
        )
    )

    if "shorts" not in data:
        raise RuntimeError(
            "Shorts seçim dosyasında "
            "'shorts' alanı bulunamadı."
        )

    if len(data["shorts"]) != 2:
        raise RuntimeError(
            "Tam olarak 2 Shorts bekleniyor."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_name = create_safe_filename(
        topic
    )

    for short in data["shorts"]:

        number = short["short"]

        schedule = short.get(
            "schedule",
            ""
        )

        english = short.get(
            "english_script",
            ""
        ).strip()

        if not english:
            raise RuntimeError(
                f"Short {number} için "
                "İngilizce metin bulunamadı."
            )

        output_file = (
            OUTPUT_DIR /
            f"{safe_name}_short_{number}_english.txt"
        )

        output_file.write_text(
            english,
            encoding="utf-8"
        )

        print(
            f"✓ Short {number} "
            f"({schedule}) altyazısı hazır."
        )

        print(
            f"  {output_file}"
        )

    print()
    print("=" * 60)
    print("ENGLISH SUBTITLE FILES HAZIR")
    print("=" * 60)


if __name__ == "__main__":
    main()
