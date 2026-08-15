import subprocess
from pathlib import Path

VIDEO_DIR = Path("research/video/shorts_final")
OUTPUT_DIR = Path("research/video/shorts_branded")


def run(command):
    print(">", " ".join(str(x) for x in command))

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError("FFmpeg işlemi başarısız oldu.")


def get_duration(video):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video)
        ],
        capture_output=True,
        text=True
    )

    return float(result.stdout.strip())


def create_brand_overlay(
    number,
    video_file,
    output_file
):

    duration = get_duration(
        video_file
    )

    # Animasyon yaklaşık videonun ortasında
    start = max(
        5,
        min(
            duration / 2,
            duration - 8
        )
    )

    end = start + 3.5

    filter_complex = (
        "[0:v]"
        "drawbox="
        "x=35:"
        "y=1600:"
        "w=430:"
        "h=105:"
        "color=black@0.82:"
        "t=fill:"
        f"enable='between(t,{start},{end})'"
        "[v1];"

        "[v1]"
        "drawtext="
        "text='SHADOW ARCHIVE':"
        "fontcolor=white:"
        "fontsize=34:"
        "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "x=65:"
        "y=1630:"
        f"enable='between(t,{start},{end})'"
        "[v2];"

        "[v2]"
        "drawtext="
        "text='ABONE OL':"
        "fontcolor=white:"
        "fontsize=25:"
        "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "x=65:"
        "y=1675:"
        f"enable='between(t,{start},{end})'"
        "[v3]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v3]",
            "-map",
            "0:a?",
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
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_file)
        ]
    )


def main():

    print("=" * 60)
    print("SHADOW ARCHIVE — SHORTS BRANDING")
    print("=" * 60)

    if not VIDEO_DIR.exists():
        raise FileNotFoundError(
            "Final Shorts klasörü bulunamadı."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for number in [1, 2]:

        video_file = (
            VIDEO_DIR /
            f"shadow_archive_short_{number}_final.mp4"
        )

        output_file = (
            OUTPUT_DIR /
            f"shadow_archive_short_{number}_branded.mp4"
        )

        if not video_file.exists():
            raise FileNotFoundError(
                f"Short {number} bulunamadı."
            )

        print()
        print(
            f"Short {number} markalanıyor..."
        )

        create_brand_overlay(
            number,
            video_file,
            output_file
        )

        print(
            f"Short {number} hazır."
        )

    print()
    print("=" * 60)
    print("SHORTS BRANDING TAMAMLANDI")
    print("=" * 60)


if __name__ == "__main__":
    main()
