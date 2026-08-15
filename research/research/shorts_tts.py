import subprocess
import json
from pathlib import Path

SELECTION_FILE = Path("research/video/shorts_selection.json")
VOICE_DIR = Path("research/voices")
OUTPUT_DIR = Path("research/audio/shorts")

VOICE = "tr_TR-dfki-medium"


def main():
    if not SELECTION_FILE.exists():
        raise FileNotFoundError(
            "Shorts seçim dosyası bulunamadı."
        )

    data = json.loads(
        SELECTION_FILE.read_text(
            encoding="utf-8"
        )
    )

    VOICE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("SHADOW ARCHIVE — SHORTS TTS")
    print("=" * 60)

    print("Türkçe ses modeli indiriliyor...")

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
        print(download.stderr)
        raise RuntimeError(
            "Piper ses modeli indirilemedi."
        )

    model_file = VOICE_DIR / f"{VOICE}.onnx"

    for short in data["shorts"]:

        number = short["short"]
        script = short["script"]

        output_file = (
            OUTPUT_DIR /
            f"short_{number}.wav"
        )

        print()
        print(
            f"Short {number} ses oluşturuluyor..."
        )

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
            print(process.stderr)
            raise RuntimeError(
                f"Short {number} TTS başarısız."
            )

        print(
            f"Short {number} hazır: {output_file}"
        )

    print()
    print("=" * 60)
    print("SHORTS SESLERİ HAZIR")
    print("=" * 60)


if __name__ == "__main__":
    main()
