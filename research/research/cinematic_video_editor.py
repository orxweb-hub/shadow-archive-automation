import json
import re
from pathlib import Path
import subprocess


TOPIC_FILE = Path(
    "research/current_topic.json"
)

AUDIO_DIR = Path(
    "research/audio"
)

CLIPS_DIR = Path(
    "research/video/clips"
)

MUSIC_FILE = Path(
    "research/audio/dead_forest.mp3"
)

WORK_DIR = Path(
    "research/video/cinematic_work_v4"
)

OUTPUT_DIR = Path(
    "research/video"
)

WIDTH = 1920
HEIGHT = 1080
FPS = 30
SEGMENT_DURATION = 7


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


def find_voice_file(topic):

    safe_name = create_safe_filename(
        topic
    )

    expected_file = (
        AUDIO_DIR /
        f"{safe_name}_voice.wav"
    )

    if expected_file.exists():

        return expected_file

    voice_files = list(
        AUDIO_DIR.glob(
            "*_voice.wav"
        )
    )

    if not voice_files:

        raise FileNotFoundError(
            "Hiçbir ses dosyası bulunamadı."
        )

    voice_files.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    return voice_files[0]


def run(cmd):

    print(
        "RUN:",
        " ".join(
            map(str, cmd)
        )
    )

    result = subprocess.run(
        cmd,
        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg/FFprobe komutu başarısız oldu."
        )


def get_duration(path):

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(
        result.stdout.strip()
    )


def main():

    print(
        "=========================================="
    )

    print(
        "SHADOW ARCHIVE CINEMATIC V4"
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

    AUDIO_FILE = find_voice_file(
        topic
    )

    safe_name = create_safe_filename(
        topic
    )

    OUTPUT_FILE = (
        OUTPUT_DIR /
        f"{safe_name}_v4.mp4"
    )

    print()
    print(
        "SES DOSYASI:"
    )
    print(AUDIO_FILE)

    print()
    print(
        "ÇIKTI:"
    )
    print(OUTPUT_FILE)

    if not AUDIO_FILE.exists():

        raise FileNotFoundError(
            f"Voice file not found: {AUDIO_FILE}"
        )

    if not MUSIC_FILE.exists():

        raise FileNotFoundError(
            f"Music file not found: {MUSIC_FILE}"
        )

    if not CLIPS_DIR.exists():

        raise FileNotFoundError(
            f"Clips directory not found: {CLIPS_DIR}"
        )

    clips = sorted(
        CLIPS_DIR.glob("*.mp4")
    )

    if not clips:

        raise FileNotFoundError(
            "No Pexels video clips found."
        )

    WORK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for old_file in WORK_DIR.glob(
        "segment_*.mp4"
    ):

        old_file.unlink()

    duration = get_duration(
        AUDIO_FILE
    )

    print()
    print(
        f"Voice duration: "
        f"{duration:.2f}s"
    )

    print(
        f"Available clips: "
        f"{len(clips)}"
    )

    print(
        f"Music: {MUSIC_FILE}"
    )

    # ==========================================
    # 1. VIDEO SEGMENTS
    # ==========================================

    segment_files = []

    total_segments = (
        int(duration / SEGMENT_DURATION)
        + 1
    )

    for i in range(
        total_segments
    ):

        clip = clips[
            i % len(clips)
        ]

        output = (
            WORK_DIR /
            f"segment_{i:04d}.mp4"
        )

        print(
            f"Creating segment "
            f"{i + 1}/{total_segments}"
        )

        vf = (
            f"scale={WIDTH}:{HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            "eq=contrast=1.06:"
            "saturation=1.05:"
            "brightness=-0.03,"
            "vignette,"
            "format=yuv420p"
        )

        run([
            "ffmpeg",
            "-y",

            "-stream_loop",
            "-1",

            "-i",
            str(clip),

            "-t",
            str(SEGMENT_DURATION),

            "-vf",
            vf,

            "-an",

            "-r",
            str(FPS),

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            "-pix_fmt",
            "yuv420p",

            "-movflags",
            "+faststart",

            str(output),
        ])

        segment_files.append(
            output
        )

    # ==========================================
    # 2. CONCAT VIDEO
    # ==========================================

    concat_file = (
        WORK_DIR /
        "concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for segment in segment_files:

            f.write(
                f"file '{segment.resolve()}'\n"
            )

    base_video = (
        WORK_DIR /
        "base_video.mp4"
    )

    print(
        "Joining video segments..."
    )

    run([
        "ffmpeg",
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-t",
        str(duration),

        "-c",
        "copy",

        "-movflags",
        "+faststart",

        str(base_video),
    ])

    # ==========================================
    # 3. VOICE + MUSIC
    # ==========================================

    mixed_audio = (
        WORK_DIR /
        "final_audio.m4a"
    )

    print(
        "Creating final audio mix..."
    )

    print(
        "Voice volume: 100%"
    )

    print(
        "Dead Forest volume: 16%"
    )

    audio_filter = (
        "[0:a]volume=1.0[voice];"
        "[1:a]volume=0.16[music];"
        "[voice][music]"
        "amix="
        "inputs=2:"
        "duration=first:"
        "dropout_transition=2"
    )

    run([
        "ffmpeg",
        "-y",

        "-i",
        str(AUDIO_FILE),

        "-stream_loop",
        "-1",

        "-i",
        str(MUSIC_FILE),

        "-filter_complex",
        audio_filter,

        "-t",
        str(duration),

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-ar",
        "44100",

        "-ac",
        "2",

        str(mixed_audio),
    ])

    # ==========================================
    # 4. ADD AUDIO
    # ==========================================

    print(
        "Adding final audio to video..."
    )

    run([
        "ffmpeg",
        "-y",

        "-i",
        str(base_video),

        "-i",
        str(mixed_audio),

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-t",
        str(duration),

        "-c:v",
        "copy",

        "-c:a",
        "copy",

        "-movflags",
        "+faststart",

        str(OUTPUT_FILE),
    ])

    # ==========================================
    # 5. CHECK OUTPUT
    # ==========================================

    print(
        "Checking final video..."
    )

    run([
        "ffprobe",
        "-v",
        "error",

        "-show_entries",
        "format=duration,size",

        "-of",
        "default=noprint_wrappers=1",

        str(OUTPUT_FILE),
    ])

    print()

    print(
        "=========================================="
    )

    print(
        "SHADOW ARCHIVE CINEMATIC V4 COMPLETE"
    )

    print(
        "=========================================="
    )

    print(
        f"Konu: {topic}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        f"Duration: {duration:.2f}s"
    )

    print(
        "Real Pexels motion: ENABLED"
    )

    print(
        "Dead Forest music: ENABLED"
    )

    print(
        "Turkish voice: ENABLED"
    )

    print(
        "1080p YouTube format: ENABLED"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
