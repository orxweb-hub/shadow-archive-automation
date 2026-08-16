import subprocess
import json
import re
from pathlib import Path


TOPIC_FILE = Path("research/current_topic.json")
SELECTION_DIR = Path("research/video")
VOICE_DIR = Path("research/voices")
OUTPUT_DIR = Path("research/audio/shorts")

VOICE = "tr_TR-dfki-medium"


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


def download_voice_model():
    print(
        "Türkçe ses modeli kontrol ediliyor..."
    )

    download = subprocess.run(
        [
            "python",
            "-m",
            "piper.download_voices",
            "--data-dir",
            str(VOICE_DIR),
            VOICE
        ],
        text=True,
        capture_output=True
    )

    if download.returncode != 0:
        print(download.stdout)
        print(download.stderr)

        raise RuntimeError(
            "Piper ses modeli indirilemedi."
        )

    model_file = (
        VOICE_DIR /
        f"{VOICE}.onnx"
    )

    if not model_file.exists():
        raise FileNotFoundError(
            f"Piper model bulunamadı: {model_file}"
        )

    return model_file


def generate_voice(
    script,
    model_file,
    output_file
):
    process = subprocess.run(
        [
            "piper",
            "--model",
            str(model_file),
            "--output_file",
            str(output_file)
        ],
        input=script,
        text=True,
        capture_output=True
    )

    if process.returncode != 0:
        print(process.stdout)
        print(process.stderr)

        raise RuntimeError(
            f"TTS başarısız: {output_file}"
        )


def main():
    topic_data = load_current_topic()

    topic = topic_data["topic"]

    selection_file = find_selection_file(
        topic
    )

    print(
        f"Shorts seçimi bulundu: {selection_file}"
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

    VOICE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_name = create_safe_filename(
        topic
    )

    print()
    print("SHADOW ARCHIVE — SHORTS TTS")
    print("=" * 60)
    print(f"Konu: {topic}")
    print()

    model_file = download_voice_model()

    for short in data["shorts"]:

        number = short["short"]
        schedule = short.get(
            "schedule",
            ""
        )
        script = short["narration"].strip()

        output_file = (
            OUTPUT_DIR /
            f"{safe_name}_short_{number}.wav"
        )

        print(
            f"Short {number} "
            f"({schedule}) ses oluşturuluyor..."
        )

        generate_voice(
            script,
            model_file,
            output_file
        )

        print(
            f"✓ Short {number} hazır:"
        )
        print(
            f"  {output_file}"
        )

    print()
    print("=" * 60)
    print("SHORTS SESLERİ HAZIR")
    print("=" * 60)


if __name__ == "__main__":
    main()
