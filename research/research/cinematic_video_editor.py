from pathlib import Path
import subprocess

CLIPS_DIR = Path("research/video/clips")
AUDIO_FILE = Path("research/audio/mv_joyita_voice.wav")
MUSIC_FILE = Path("research/audio/dead_forest.mp3")

WORK_DIR = Path("research/video/cinematic_work_v4")
OUTPUT_FILE = Path("research/video/shadow_archive_mv_joyita_v4.mp4")

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
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def main():

    if not AUDIO_FILE.exists():
        raise FileNotFoundError(f"Voice file not found: {AUDIO_FILE}")

    if not MUSIC_FILE.exists():
        raise FileNotFoundError(f"Music file not found: {MUSIC_FILE}")

    if not CLIPS_DIR.exists():
        raise FileNotFoundError(f"Clips directory not found: {CLIPS_DIR}")

    clips = sorted(CLIPS_DIR.glob("*.mp4"))

    if not clips:
        raise FileNotFoundError("No Pexels video clips found.")

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    for old_file in WORK_DIR.glob("segment_*.mp4"):
        old_file.unlink()

    duration = get_duration(AUDIO_FILE)

    print(f"Voice duration: {duration:.2f}s")
    print(f"Available clips: {len(clips)}")
    print(f"Music: {MUSIC_FILE}")

    segment_files = []

    total_segments = int(duration / SEGMENT_DURATION) + 1

    for i in range(total_segments):

        clip = clips[i % len(clips)]
        output = WORK_DIR / f"segment_{i:04d}.mp4"

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
            "-stream_loop", "-1",
            "-i", str(clip),
            "-t", str(SEGMENT_DURATION),
            "-vf", vf,
            "-an",
            "-r", str(FPS),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output),
        ])

        segment_files.append(output)

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
        "-movflags", "+faststart",
        str(base_video),
    ])

    print("Mixing voice + Dead Forest music...")

    audio_filter = (
        "[1:a]volume=0.16,"
        "afade=t=in:st=0:d=4,"
        "afade=t=out:st=1730:d=10"
        "[music];"
        "[2:a]volume=1.0[voice];"
        "[voice][music]"
        "amix=inputs=2:"
        "duration=first:"
        "dropout_transition=2:"
        "normalize=0,"
        "alimiter=limit=0.95"
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

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",

        "-movflags", "+faststart",

        str(OUTPUT_FILE),
    ])

    print("")
    print("==========================================")
    print("SHADOW ARCHIVE CINEMATIC V4 COMPLETE")
    print("==========================================")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Duration: {duration:.2f}s")
    print("Real video motion: ENABLED")
    print("Dead Forest music: ENABLED")
    print("iPad compatibility: ENABLED")
    print("==========================================")


if __name__ == "__main__":
    main()
