import re
import subprocess
from pathlib import Path


SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
RAW_AUDIO_FILE = Path("research/audio/mv_joyita_voice_raw.wav")
OUTPUT_FILE = Path("research/audio/mv_joyita_voice.wav")

VOICE = "tr_TR-dfki-medium"
VOICE_DIR = Path("research/voices")


def prepare_text(text):
    """
    TTS metnini daha doğal konuşulabilecek hale getirir.

    Çok uzun cümlelerde küçük duraklamalar oluşturur.
    Noktalama işaretlerinden sonra doğal boşluk bırakır.
    """

    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    # Cümle sonlarında Piper'ın doğal duraklamasını destekle
    text = re.sub(r"([.!?])\s+", r"\1  ", text)

    # Virgüllerden sonra hafif nefes/duraklama
    text = re.sub(r",\s+", ",  ", text)

    # Çok uzun cümleleri küçük parçalara ayır
    text = re.sub(
        r"(\S{20,}),\s+",
        r"\1,  ",
        text
    )

    return text.strip()


def run(command):
    print("RUN:", " ".join(command))

    result = subprocess.run(
        command,
        text=True,
        capture_output=True
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)

        raise RuntimeError(
            "Komut çalıştırılamadı."
        )


def generate_piper_audio(text):

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
    print("Ham anlatıcı sesi oluşturuluyor...")

    model_file = VOICE_DIR / f"{VOICE}.onnx"

    process = subprocess.run(
        [
            "piper",
            "--model",
            str(model_file),
            "--output_file",
            str(RAW_AUDIO_FILE)
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

    print("Ham ses hazır.")


def improve_voice():

    print()
    print("V3 doğal ses işlemesi başlıyor...")

    # Amaç:
    # - hafif EQ
    # - konuşmayı öne çıkarma
    # - doğal ses yüksekliği
    # - hafif kompresyon
    # - çok küçük stereo genişlik
    # - yumuşak limiter
    #
    # Aşırı efekt kullanılmıyor.
    # Amaç robotik sesi efektle gizlemek değil,
    # anlatımı daha temiz ve canlı hale getirmek.

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
            str(RAW_AUDIO_FILE),
            "-af",
            audio_filter,
            "-ar",
            "44100",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(OUTPUT_FILE)
        ]
    )

    print("V3 ses işlemesi tamamlandı.")


def main():

    print("=" * 60)
    print("SHADOW ARCHIVE — NATURAL TTS V3")
    print("=" * 60)

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

    print(
        f"Senaryo uzunluğu: {len(text)} karakter"
    )

    prepared_text = prepare_text(text)

    generate_piper_audio(
        prepared_text
    )

    improve_voice()

    print()
    print("=" * 60)
    print("NATURAL TTS V3 TAMAMLANDI")
    print("=" * 60)
    print(f"Çıktı: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
