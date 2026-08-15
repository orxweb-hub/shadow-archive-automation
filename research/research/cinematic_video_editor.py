from pathlib import Path
import subprocess
import re
import shutil

CLIPS_DIR = Path("research/video/clips")
AUDIO_FILE = Path("research/audio/mv_joyita_voice.wav")
MUSIC_FILE = Path("research/audio/shorts/mystery_ambient.wav")

WORK_DIR = Path("research/video/cinematic_work_v3")
OUTPUT_FILE = Path("research/video/shadow_archive_mv_joyita_v3.mp4")

WIDTH = 1920
HEIGHT = 1080
FPS = 30
SEGMENT_DURATION = 7


def run(cmd):
    print("RUN:", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def get_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path)
        ],
        capture_output=True,
        text=True,
        check=True
    )
    return float(result.stdout.strip())


def main():
    if not AUDIO_FILE.exists():
        raise FileNotFoundError(f"Voice file not found: {AUDIO_FILE}")

    clips = sorted(CLIPS_DIR.glob("*.mp4"))

    if not clips:
        raise FileNotFoundError("No visual clips found.")

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    duration = get_duration(AUDIO_FILE)

    print(f"Voice duration: {duration:.2f}s")
    print(f"Visual clips: {len(clips)}")

    # Create cinematic segments
    segment_files = []

    total_segments = int(duration / SEGMENT_DURATION) + 1

    for i in range(total_segments):
        clip = clips[i % len(clips)]
        output = WORK_DIR / f"segment_{i:04d}.mp4"

        zoom_direction = i % 4

        if zoom_direction == 0:
            vf = (
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},"
                "zoompan="
                f"z='min(zoom+0.0018,1.12)':"
                f"x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':"
                f"d=210:s={WIDTH}x{HEIGHT}:fps={FPS},"
                "eq=contrast=1.06:saturation=1.08:brightness=-0.03,"
                "vignette"
            )

        elif zoom_direction == 1:
            vf = (
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},"
                "zoompan="
                f"z='min(zoom+0.0015,1.10)':"
                f"x='iw/2-(iw/zoom/2)+18*t':"
                f"y='ih/2-(ih/zoom/2)':"
                f"d=210:s={WIDTH}x{HEIGHT}:fps={FPS},"
                "eq=contrast=1.07:saturation=1.05:brightness=-0.04,"
                "vignette"
            )

        elif zoom_direction == 2:
            vf = (
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},"
                "zoompan="
                f"z='min(zoom+0.0015,1.10)':"
                f"x='iw/2-(iw/zoom/2)-18*t':"
                f"y='ih/2-(ih/zoom/2)':"
                f"d=210:s={WIDTH}x{HEIGHT}:fps={FPS},"
                "eq=contrast=1.08:saturation=1.06:brightness=-0.05,"
                "vignette"
            )

        else:
            vf = (
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},"
                "zoompan="
                f"z='min(zoom+0.0017,1.11)':"
                f"x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)+12*t':"
                f"d=210:s={WIDTH}x{HEIGHT}:fps={FPS},"
                "eq=contrast=1.07:saturation=1.07:brightness=-0.04,"
                "vignette"
            )

        run([
            "ffmpeg",
            "-y",
            "-stream_loop", "-1",
            "-i", str(clip),
            "-t", str(SEGMENT_DURATION),
            "-vf", vf,
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "24",
            "-pix_fmt", "yuv420p",
            str(output)
        ])

        segment_files.append(output)

    # Concat file
    concat_file = WORK_DIR / "concat.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for segment in segment_files:
            f.write(f"file '{segment.resolve()}'\n")

    base_video = WORK_DIR / "base_video.mp4"

    run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-t", str(duration),
        "-c", "copy",
        str(base_video)
    ])

    # Audio mix
    if MUSIC_FILE.exists():
        audio_filter = (
            "[2:a]"
            "volume=1.0"
            "[voice];"

            "[1:a]"
            "volume=0.35"
            "[music];"

            "[voice][music]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=3,"
            "loudnorm=I=-16:"
            "TP=-1.5:"
            "LRA=11"
            "[audio]"
        )

        run([
            "ffmpeg",
            "-y",
            "-i", str(base_video),
            "-stream_loop", "-1",
            "-i", str(MUSIC_FILE),
            "-i", str(AUDIO_FILE),
            "-filter_complex", audio_filter,
            "-map", "0:v:0",
            "-map", "[audio]",
            "-t", str(duration),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "160k",
            "-shortest",
            str(OUTPUT_FILE)
        ])

    else:
        run([
            "ffmpeg",
            "-y",
            "-i", str(base_video),
            "-i", str(AUDIO_FILE),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", str(duration),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "160k",
            str(OUTPUT_FILE)
        ])

    print("")
    print("====================================")
    print("CINEMATIC VIDEO V3 COMPLETE")
    print(f"OUTPUT: {OUTPUT_FILE}")
    print("====================================")


if __name__ == "__main__":
    main()
