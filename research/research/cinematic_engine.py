import subprocess
from pathlib import Path


INPUT_DIR = Path("research/video/clips")
OUTPUT_DIR = Path("research/video/cinematic_test")

WIDTH = 1920
HEIGHT = 1080
FPS = 30


def run(command):
    print("RUN:", " ".join(command))
    subprocess.run(command, check=True)


def create_cinematic_clip(input_file, output_file, duration):
    zoom_filter = (
        f"scale={WIDTH*2}:{HEIGHT*2}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH*2}:{HEIGHT*2},"
        f"zoompan="
        f"z='min(zoom+0.0008,1.12)':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d=1:"
        f"s={WIDTH}x{HEIGHT}:"
        f"fps={FPS},"
        f"trim=duration={duration},"
        f"setpts=PTS-STARTPTS"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-vf",
        zoom_filter,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        str(output_file),
    ]

    run(command)


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    clips = sorted(
        INPUT_DIR.glob("*.mp4")
    )

    if not clips:
        raise RuntimeError(
            "Pexels video klipleri bulunamadı."
        )

    print("=" * 60)
    print("SHADOW ARCHIVE — CINEMATIC ENGINE V2")
    print("=" * 60)

    test_clips = clips[:3]

    for index, clip in enumerate(test_clips, start=1):
        output = (
            OUTPUT_DIR /
            f"cinematic_test_{index}.mp4"
        )

        print()
        print(
            f"Klip {index}: {clip.name}"
        )

        create_cinematic_clip(
            clip,
            output,
            duration=6
        )

    print()
    print("=" * 60)
    print("CINEMATIC TEST KLİPLERİ HAZIR")
    print("=" * 60)


if __name__ == "__main__":
    main()
