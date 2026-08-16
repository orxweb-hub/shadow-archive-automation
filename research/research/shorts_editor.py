import json
import re
import subprocess
from pathlib import Path


TOPIC_FILE = Path("research/current_topic.json")
VIDEO_DIR = Path("research/video")
CLIPS_DIR = VIDEO_DIR / "clips"
AUDIO_DIR = Path("research/audio/shorts")
SELECTION_DIR = VIDEO_DIR
OUTPUT_DIR = VIDEO_DIR / "shorts"

WIDTH = 1080
HEIGHT = 1920


def create_safe_filename(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")

    if not text:
        text = "daily_topic"

    return text[:80]


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


def get_audio_duration(audio_file):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_file)
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Ses süresi okunamadı."
        )

    return float(
        result.stdout.strip()
    )


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


def find_clips():
    clips = sorted(
        CLIPS_DIR.glob("*.mp4")
    )

    if not clips:
        raise RuntimeError(
            "Pexels görüntüleri bulunamadı."
        )

    return clips


def create_short(
    topic,
    short_number,
    schedule,
    audio_file,
    clips
):
    safe_name = create_safe_filename(
        topic
    )

    duration = get_audio_duration(
        audio_file
    )

    output_file = (
        OUTPUT_DIR /
        f"{safe_name}_short_{short_number}.mp4"
    )

    selected_clips = []

    current = 0.0
    index = 0

    while current < duration:

        clip = clips[
            index % len(clips)
        ]

        remaining = (
            duration - current
        )

        clip_duration = min(
            6.0,
            remaining
        )

        selected_clips.append(
            {
                "file": clip,
                "duration": clip_duration
            }
        )

        current += clip_duration
        index += 1

    print()
    print(
        f"SHORT {short_number} "
        f"| {schedule}"
    )
    print(
        f"Süre: {duration:.1f} saniye"
    )

    segment_dir = (
        OUTPUT_DIR /
        f"{safe_name}_segments_{short_number}"
    )

    segment_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    segments = []

    for number, item in enumerate(
        selected_clips,
        start=1
    ):

        segment = (
            segment_dir /
            f"segment_{number:03d}.mp4"
        )

        filter_complex = (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "zoompan="
            "z='min(zoom+0.0012,1.10)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30,"
            "setsar=1"
        )

        run(
            [
                "ffmpeg",
                "-y",
                "-stream_loop",
                "-1",
                "-i",
                str(item["file"]),
                "-t",
                str(item["duration"]),
                "-vf",
                filter_complex,
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                str(segment)
            ]
        )

        segments.append(
            segment
        )

    concat_file = (
        OUTPUT_DIR /
        f"{safe_name}_concat_{short_number}.txt"
    )

    with concat_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        for segment in segments:

            path = segment.resolve()

            file.write(
                f"file '{path}'\n"
            )

    silent_video = (
        OUTPUT_DIR /
        f"{safe_name}_silent_short_{short_number}.mp4"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(silent_video)
        ]
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(audio_file),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_file)
        ]
    )

    print(
        f"✓ SHORT {short_number} HAZIR:"
    )
    print(
        f"  {output_file}"
    )


def main():

    print("=" * 60)
    print(
        "SHADOW ARCHIVE — SHORTS VIDEO EDITOR"
    )
    print("=" * 60)

    topic_data = load_current_topic()

    topic = topic_data["topic"]

    selection_file = find_selection_file(
        topic
    )

    print(
        f"Konu: {topic}"
    )

    print(
        f"Shorts seçimi: {selection_file}"
    )

    if not AUDIO_DIR.exists():
        raise FileNotFoundError(
            "Shorts ses klasörü bulunamadı."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    data = json.loads(
        selection_file.read_text(
            encoding="utf-8"
        )
    )

    if "shorts" not in data:
        raise RuntimeError(
            "Shorts seçim dosyasında "
            "'shorts' bulunamadı."
        )

    if len(data["shorts"]) != 2:
        raise RuntimeError(
            "Tam olarak 2 Shorts bekleniyor."
        )

    clips = find_clips()

    print(
        f"Pexels klip sayısı: {len(clips)}"
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

        audio_file = (
            AUDIO_DIR /
            f"{safe_name}_short_{number}.wav"
        )

        if not audio_file.exists():
            raise FileNotFoundError(
                f"Short {number} ses dosyası bulunamadı: "
                f"{audio_file}"
            )

        create_short(
            topic,
            number,
            schedule,
            audio_file,
            clips
        )

    print()
    print("=" * 60)
    print(
        "SHORTS VİDEO ÜRETİMİ TAMAMLANDI"
    )
    print("=" * 60)

    for file in sorted(
        OUTPUT_DIR.glob(
            f"{safe_name}_short_*.mp4"
        )
    ):
        print(file)


if __name__ == "__main__":
    main()
