import re
import subprocess
import json
from pathlib import Path


TOPIC_FILE = Path(
    "research/current_topic.json"
)

SCRIPT_DIR = Path(
    "research/scripts"
)

AUDIO_DIR = Path(
    "research/audio"
)

VOICE = "tr_TR-dfki-medium"

VOICE_DIR = Path(
    "research/voices"
)


def create_safe_filename(text):

    filename = text.lower()

    filename = re.sub(
        r"[^a-z0-9]+",
        "_",
        filename
    )

    filename = filename.strip("_")

    if not filename:
        filename = "daily_topic"

    return filename[:80]


def load_current_topic():

    if not TOPIC_FILE.exists():

        raise FileNotFoundError(
            f"Güncel konu bulunamadı: {TOPIC_FILE}"
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

    return topic


def find_script(topic):

    safe_name = create_safe_filename(
        topic
    )

    expected_file = (
        SCRIPT_DIR /
        f"{safe_name}_script.txt"
    )

    if expected_file.exists():

        return expected_file

    scripts = list(
        SCRIPT_DIR.glob(
            "*_script.txt"
        )
    )

    if not scripts:

        raise FileNotFoundError(
            "Hiçbir senaryo dosyası bulunamadı."
        )

    scripts.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    return scripts[0]


def prepare_text(text):

    text = text.replace(
        "\r\n",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"([.!?])\s+",
        r"\1  ",
        text
    )

    text = re.sub(
        r",\s+",
        ",  ",
        text
    )

    text = re.sub(
        r"(\S{20,}),\s+",
        r"\1,  ",
        text
    )

    return text.strip()


def run(command):

    print(
        "RUN:",
        " ".join(
            map(str, command)
        )
    )

    result = subprocess.run(
        command,
        text=True,
        capture_output=True
    )

    if result.stdout:
        print(
            result.stdout
        )

    if result.returncode != 0:

        if result.stderr:
            print(
                result.stderr
            )

        raise RuntimeError(
            "Komut çalıştırılamadı."
        )


def generate_piper_audio(
    text,
    raw_audio_file
):

    print(
        "Türkçe ses modeli indiriliyor..."
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

    print(
        download.stdout
    )

    if download.returncode != 0:

        print(
            download.stderr
        )

        raise RuntimeError(
            "Piper ses modeli indirilemedi."
        )

    print(
        "Ses modeli hazır."
    )

    print(
        "Ham anlatıcı sesi oluşturuluyor..."
    )

    model_file = (
        VOICE_DIR /
        f"{VOICE}.onnx"
    )

    process = subprocess.run(
        [
            "piper",
            "--model",
            str(model_file),
            "--output_file",
            str(raw_audio_file)
        ],
        input=text,
        text=True,
        capture_output=True
    )

    if process.returncode != 0:

        print(
            process.stderr
        )

        raise RuntimeError(
            "Piper TTS çalıştırılamadı."
        )

    print(
        "Ham ses hazır."
    )


def improve_voice(
    raw_audio_file,
    output_file
):

    print()
    print(
        "V3 doğal ses işlemesi başlıyor..."
    )

    audio_filter = (
        "highpass=f=70,"
        "lowpass=f=12000,"
        "equalizer=f=180:t=q:w=1:g=1.2,"
        "equalizer=f=3200:t=q:w=1:g=1.5,"
        "acompressor="
        "threshold=-20dB:"
        "ratio=2.2:"
        "attack=12:"
        "release=90:"
        "makeup=1.5,"
        "volume=1.8,"
        "alimiter=limit=0.92:"
        "attack=5:"
        "release=80"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_audio_file),
            "-af",
            audio_filter,
            "-ar",
            "44100",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(output_file)
        ]
    )

    print(
        "V3 ses işlemesi tamamlandı."
    )


def main():

    print("=" * 60)
    print(
        "SHADOW ARCHIVE — NATURAL TTS V3"
    )
    print("=" * 60)

    topic = load_current_topic()

    print()
    print(
        "GÜNCEL KONU:"
    )
    print(topic)

    print()

    script_file = find_script(
        topic
    )

    print(
        "SENARYO:"
    )
    print(script_file)

    safe_name = create_safe_filename(
        topic
    )

    AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    VOICE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    raw_audio_file = (
        AUDIO_DIR /
        f"{safe_name}_voice_raw.wav"
    )

    output_file = (
        AUDIO_DIR /
        f"{safe_name}_voice.wav"
    )

    text = script_file.read_text(
        encoding="utf-8"
    )

    if not text.strip():

        raise RuntimeError(
            "Senaryo dosyası boş."
        )

    print()
    print(
        f"Senaryo uzunluğu: "
        f"{len(text)} karakter"
    )

    prepared_text = prepare_text(
        text
    )

    generate_piper_audio(
        prepared_text,
        raw_audio_file
    )

    improve_voice(
        raw_audio_file,
        output_file
    )

    print()
    print("=" * 60)
    print(
        "NATURAL TTS V3 TAMAMLANDI"
    )
    print("=" * 60)

    print(
        f"Konu: {topic}"
    )

    print(
        f"Çıktı: {output_file}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
