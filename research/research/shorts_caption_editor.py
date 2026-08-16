import json
import re
import subprocess
from pathlib import Path


TOPIC_FILE = Path("research/current_topic.json")

VIDEO_DIR = Path("research/video/shorts")
SUBTITLE_DIR = Path("research/video/subtitles")
OUTPUT_DIR = Path("research/video/shorts_final")


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


def run(command):
    print(
        ">",
        " ".join(str(x) for x in command)
    )

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg işlemi başarısız oldu."
        )


def get_video_duration(video_file):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_file)
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Video süresi okunamadı: {video_file}"
        )

    return float(
        result.stdout.strip()
    )


def create_subtitle_file(
    text_file,
    srt_file,
    video_file
):
    text = text_file.read_text(
        encoding="utf-8"
    ).strip()

    if not text:
        raise RuntimeError(
            f"Altyazı boş: {text_file}"
        )

    words = text.split()

    chunks = []
    current = []

    for word in words:

        current.append(word)

        if len(current) >= 4:
            chunks.append(
                " ".join(current)
            )
            current = []

    if current:
        chunks.append(
            " ".join(current)
        )

    total_seconds = get_video_duration(
        video_file
    )

    chunk_duration = (
        total_seconds /
        max(len(chunks), 1)
    )

    def timestamp(seconds):

        hours = int(
            seconds // 3600
        )

        minutes = int(
            (seconds % 3600) // 60
        )

        secs = int(
            seconds % 60
        )

        millis = int(
            (seconds - int(seconds)) * 1000
        )

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d},"
            f"{millis:03d}"
        )

    with srt_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        for index, chunk in enumerate(
            chunks,
            start=1
        ):

            start = (
                index - 1
            ) * chunk_duration

            end = (
                index *
                chunk_duration
            )

            file.write(
                f"{index}\n"
            )

            file.write(
                f"{timestamp(start)} --> "
                f"{timestamp(end)}\n"
            )

            file.write(
                f"{chunk}\n\n"
            )


def burn_subtitles(
    video_file,
    srt_file,
    output_file
):

    subtitle_path = (
        str(srt_file)
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )

    filter_text = (
        f"subtitles='{subtitle_path}':"
        "force_style="
        "'FontName=DejaVu Sans,"
        "FontSize=18,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=180'"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-vf",
            filter_text,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_file)
        ]
    )


def main():

    print("=" * 60)
    print(
        "SHADOW ARCHIVE — SHORTS CAPTION EDITOR"
    )
    print("=" * 60)

    topic_data = load_current_topic()

    topic = topic_data["topic"]

    safe_name = create_safe_filename(
        topic
    )

    print(
        f"Konu: {topic}"
    )

    if not VIDEO_DIR.exists():
        raise FileNotFoundError(
            "Shorts video klasörü bulunamadı."
        )

    if not SUBTITLE_DIR.exists():
        raise FileNotFoundError(
            "Subtitle klasörü bulunamadı."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for number in [1, 2]:

        video_file = (
            VIDEO_DIR /
            f"{safe_name}_short_{number}.mp4"
        )

        text_file = (
            SUBTITLE_DIR /
            f"{safe_name}_short_{number}_english.txt"
        )

        srt_file = (
            OUTPUT_DIR /
            f"{safe_name}_short_{number}.srt"
        )

        output_file = (
            OUTPUT_DIR /
            f"{safe_name}_short_{number}_final.mp4"
        )

        if not video_file.exists():
            raise FileNotFoundError(
                f"Short {number} videosu bulunamadı: "
                f"{video_file}"
            )

        if not text_file.exists():
            raise FileNotFoundError(
                f"Short {number} altyazısı bulunamadı: "
                f"{text_file}"
            )

        print()
        print(
            f"SHORT {number} altyazı hazırlanıyor..."
        )

        create_subtitle_file(
            text_file,
            srt_file,
            video_file
        )

        print(
            f"SHORT {number} videoya işleniyor..."
        )

        burn_subtitles(
            video_file,
            srt_file,
            output_file
        )

        print(
            f"✓ SHORT {number} TAMAMLANDI"
        )

    print()
    print("=" * 60)
    print(
        "SHORTS V2 TAMAMLANDI"
    )
    print("=" * 60)

    for file in sorted(
        OUTPUT_DIR.glob(
            f"{safe_name}_short_*_final.mp4"
        )
    ):
        print(file)


if __name__ == "__main__":
    main()
