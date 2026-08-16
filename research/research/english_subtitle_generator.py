import json
import re
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import whisper


TOPIC_FILE = Path(
    "research/current_topic.json"
)

AUDIO_DIR = Path(
    "research/audio"
)

SUBTITLE_DIR = Path(
    "research/video/subtitles"
)

MODEL_NAME = (
    "Helsinki-NLP/opus-mt-tr-en"
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


def find_audio_file(topic):

    safe_name = create_safe_filename(
        topic
    )

    expected_file = (
        AUDIO_DIR /
        f"{safe_name}_voice.wav"
    )

    if expected_file.exists():

        return expected_file

    audio_files = list(
        AUDIO_DIR.glob(
            "*_voice.wav"
        )
    )

    if not audio_files:

        raise FileNotFoundError(
            "Hiçbir Türkçe ses dosyası bulunamadı."
        )

    audio_files.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    return audio_files[0]


def format_time(seconds):

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = (
        milliseconds // 3600000
    )

    milliseconds %= 3600000

    minutes = (
        milliseconds // 60000
    )

    milliseconds %= 60000

    seconds = (
        milliseconds // 1000
    )

    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d},"
        f"{milliseconds:03d}"
    )


def translate_text(
    text,
    tokenizer,
    model,
    device
):

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

    translated = (
        tokenizer.batch_decode(
            output,
            skip_special_tokens=True
        )[0]
    )

    return translated.strip()


def main():

    print(
        "=========================================="
    )

    print(
        "SHADOW ARCHIVE ENGLISH SUBTITLES"
    )

    print(
        "=========================================="
    )

    topic = load_current_topic()

    print()
    print(
        "GÜNCEL KONU:"
    )

    print(topic)

    print()

    audio_file = find_audio_file(
        topic
    )

    safe_name = create_safe_filename(
        topic
    )

    output_file = (
        SUBTITLE_DIR /
        f"{safe_name}_english.srt"
    )

    print(
        "SES DOSYASI:"
    )

    print(audio_file)

    print()

    print(
        "ALTYAZI DOSYASI:"
    )

    print(output_file)

    if not audio_file.exists():

        raise FileNotFoundError(
            f"Audio not found: {audio_file}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ==========================================
    # DEVICE
    # ==========================================

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print()
    print(
        f"Device: {device}"
    )

    # ==========================================
    # WHISPER
    # ==========================================

    print()
    print(
        "Loading Whisper..."
    )

    whisper_model = whisper.load_model(
        "base"
    )

    print(
        "Transcribing Turkish audio..."
    )

    result = whisper_model.transcribe(

        str(audio_file),

        language="tr",

        task="transcribe",

        fp16=torch.cuda.is_available()

    )

    segments = result[
        "segments"
    ]

    print(
        f"Detected segments: "
        f"{len(segments)}"
    )

    # ==========================================
    # TRANSLATION MODEL
    # ==========================================

    print()
    print(
        "Loading Turkish -> English model..."
    )

    tokenizer = (
        AutoTokenizer.from_pretrained(
            MODEL_NAME
        )
    )

    translation_model = (
        AutoModelForSeq2SeqLM
        .from_pretrained(
            MODEL_NAME
        )
        .to(device)
    )

    translation_model.eval()

    # ==========================================
    # TRANSLATE
    # ==========================================

    subtitles = []

    for index, segment in enumerate(
        segments,
        start=1
    ):

        start = float(
            segment["start"]
        )

        end = float(
            segment["end"]
        )

        turkish = (
            segment["text"]
            .strip()
        )

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

    # ==========================================
    # WRITE SRT
    # ==========================================

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        for index, (
            start,
            end,
            text
        ) in enumerate(
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

    print()
    print(
        "=========================================="
    )

    print(
        "ENGLISH SUBTITLES COMPLETE"
    )

    print(
        "=========================================="
    )

    print(
        f"Topic: {topic}"
    )

    print(
        f"Audio: {audio_file}"
    )

    print(
        f"Output: {output_file}"
    )

    print(
        f"Subtitles: {len(subtitles)}"
    )

    print(
        "Gemini: NOT USED"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
