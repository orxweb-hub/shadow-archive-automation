import subprocess
from pathlib import Path


SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
OUTPUT_FILE = Path("research/audio/mv_joyita_voice.wav")

VOICE = "tr_TR-dfki-medium"


def main():

    if not SCRIPT_FILE.exists():
        raise FileNotFoundError(
            f"Senaryo bulunamadı: {SCRIPT_FILE}"
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
    print("Türkçe ses oluşturuluyor...")

    process = subprocess.run(
        [
            "piper",
            "--model",
            VOICE,
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
