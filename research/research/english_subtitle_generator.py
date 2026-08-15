import subprocess
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import whisper


AUDIO_FILE = Path("research/audio/mv_joyita_voice.wav")
OUTPUT_FILE = Path("research/video/subtitles/mv_joyita_english.srt")

MODEL_NAME = "Helsinki-NLP/opus-mt-tr-en"


def format_time(seconds):
    milliseconds = int(round(seconds * 1000))

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    seconds = milliseconds // 1000
    milliseconds %= 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def translate_text(text, tokenizer, model, device):
    if not text.strip():
        return ""

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=128,
            num_beams=4
        )

    translated = tokenizer.batch_decode(
        output,
        skip_special_tokens=True
    )[0]

    return translated.strip()


def main():

    if not AUDIO_FILE.exists():
        raise FileNotFoundError(
            f"Audio not found: {AUDIO_FILE}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print("==========================================")
    print("SHADOW ARCHIVE ENGLISH SUBTITLES")
    print("==========================================")

    # ----------------------------------------
    # DEVICE
    # ----------------------------------------

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Device: {device}")

    # ----------------------------------------
    # WHISPER
    # Turkish speech recognition ONLY
    # ----------------------------------------

    print("")
    print("Loading Whisper...")

    whisper_model = whisper.load_model("base")

    print("Transcribing Turkish audio...")

    result = whisper_model.transcribe(
        str(AUDIO_FILE),
        language="tr",
        task="transcribe",
        fp16=torch.cuda.is_available()
    )

    segments = result["segments"]

    print(f"Detected segments: {len(segments)}")

    # ----------------------------------------
    # TRANSLATION MODEL
    # ----------------------------------------

    print("")
    print("Loading Turkish -> English model...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    translation_model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME
    ).to(device)

    translation_model.eval()

    # ----------------------------------------
    # TRANSLATE SEGMENTS
    # ----------------------------------------

    subtitles = []

    for index, segment in enumerate(segments, start=1):

        start = float(segment["start"])
        end = float(segment["end"])
        turkish = segment["text"].strip()

        if not turkish:
            continue

        print(
            f"[{index}/{len(segments)}] "
            f"{turkish}"
        )

        english = translate_text(
            turkish,
            tokenizer,
            translation_model,
            device
        )

        if not english:
            continue

        subtitles.append(
            (
                start,
                end,
                english
            )
        )

    # ----------------------------------------
    # WRITE SRT
    # ----------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for index, (start, end, text) in enumerate(
            subtitles,
            start=1
        ):

            file.write(
                f"{index}\n"
            )

            file.write(
                f"{format_time(start)} --> "
                f"{format_time(end)}\n"
            )

            file.write(
                f"{text}\n\n"
            )

    print("")
    print("==========================================")
    print("ENGLISH SUBTITLES COMPLETE")
    print("==========================================")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Subtitles: {len(subtitles)}")
    print("Gemini: NOT USED")
    print("==========================================")


if __name__ == "__main__":
    main()
