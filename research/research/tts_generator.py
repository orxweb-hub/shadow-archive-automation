import subprocess
from pathlib import Path


SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
OUTPUT_FILE = Path("research/audio/mv_joyita_voice.wav")

VOICE = "tr_TR-dfki-medium"
VOICE_DIR = Path("research/voices")


def main():

    if not SCRIPT_FILE.exists():
        raise FileNotFoundError(
            f"Senaryo bulunamadı: {SCRIPT_FILE}"
        )

    VOICE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    text = SCRIPT_FILE.read_text(
        encoding="utf-8"
    )

    if not text.strip():
        raise RuntimeError(
            "Senaryo dosyası boş."
        )

    print("SHADOW ARCHIVE — TTS")
    print("=" * 50)

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

    print(download.stdout)

    if download.returncode != 0:
        print(download.stderr)
        raise RuntimeError(
            "Piper ses modeli indirilemedi."
        )

    print("Ses modeli hazır.")
    print("Türkçe ses oluşturuluyor...")

    model_file = VOICE_DIR / f"{VOICE}.onnx"

    process = subprocess.run(
        [
            "piper",
            "--model",
            str(model_file),
            "--output_file",
            str(OUTPUT_FILE)
        ],
        input=text,
        text=True,
        capture_output=True
    )

    if process.returncode != 0:
        print(process.stderr)
        raise RuntimeError(
            "Piper TTS çalıştırılamadı."
        )

    print()
    print("SES OLUŞTURULDU")
    print("=" * 50)
    print(f"Dosya: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
