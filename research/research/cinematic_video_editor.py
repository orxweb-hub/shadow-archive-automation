import subprocess
from pathlib import Path


CLIPS_DIR = Path("research/video/clips")
AUDIO_FILE = Path("research/audio/mv_joyita_voice.wav")
MUSIC_FILE = Path("research/audio/shorts/mystery_ambient.wav")

WORK_DIR = Path("research/video/cinematic_work")
OUTPUT_FILE = Path("research/video/shadow_archive_mv_joyita_v2.mp4")

WIDTH = 1920
HEIGHT = 1080
FPS = 30


def run(command):
    print("RUN:", " ".join(command))
    subprocess.run(command, check=True)


def get_audio_duration():
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(AUDIO_FILE),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(result.stdout.strip())


def create_segment(input_file, output_file, duration, index):

    if index % 3 == 0:
        zoom = "min(zoom+0.0007,1.10)"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"

    elif index % 3 == 1:
        zoom = "min(zoom+0.0005,1.08)"
        x = "iw/2-(iw/zoom/2)+sin(on/18)*25"
        y = "ih/2-(ih/zoom/2)"

    else:
        zoom = "min(zoom+0.0006,1.09)"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)+sin(on/20)*18"

    vf = (
        f"scale={WIDTH*2}:{HEIGHT*2}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH*2}:{HEIGHT*2},"
        f"zoompan=z='{zoom}':"
        f"x='{x}':"
        f"y='{y}':"
        "d=1:"
        f"s={WIDTH}x{HEIGHT}:"
        f"fps={FPS},"
        f"trim=duration={duration},"
        "setpts=PTS-STARTPTS,"
        "eq=contrast=1.04:saturation=0.92:brightness=-0.015,"
        "vignette=PI/5"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_file),
            "-vf",
            vf,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            str(output_file),
        ]
    )


def create_segments(duration):

    clips = sorted(
        CLIPS_DIR.glob("*.mp4")
    )

    if not clips:
        raise RuntimeError(
            "Pexels klipleri bulunamadı."
        )

    segment_duration = 7.0
    count = int(duration / segment_duration) + 1

    segments = []

    for index in range(count):

        clip = clips[index % len(clips)]

        output = (
            WORK_DIR /
            f"segment_{index:04d}.mp4"
        )

        create_segment(
            clip,
            output,
            segment_duration,
            index
        )

        segments.append(output)

    return segments


def create_concat_file(segments):

    concat_file = WORK_DIR / "concat.txt"

    with concat_file.open(
        "w",
        encoding="utf-8"
    ) as f:

        for segment in segments:
            f.write(
                f"file '{segment.resolve()}'\n"
            )

    return concat_file


def build_video(concat_file, duration):

    base_video = WORK_DIR / "base_video.mp4"

    print("Video birleştiriliyor...")

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
            "-t",
            str(duration),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            str(base_video),
        ]
    )

    print("Ses ve gizemli müzik ekleniyor...")

    if MUSIC_FILE.exists():

        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(base_video),
                "-stream_loop",
                "-1",
                "-i",
                str(MUSIC_FILE),
                "-i",
                str(AUDIO_FILE),
                "-filter_complex",
                (
                    "[2:a]volume=1.0[voice];"
                    "[1:a]volume=0.055[music];"
                    "[voice][music]"
                    "amix=inputs=2:"
                    "duration=first:"
                    "dropout_transition=3"
                    "[audio]"
                ),
                "-map",
                "0:v",
                "-map",
                "[audio]",
                "-t",
                str(duration),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-shortest",
                str(OUTPUT_FILE),
            ]
        )

    else:

        print(
            "Müzik bulunamadı. "
            "Sadece anlatıcı kullanılacak."
        )

        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(base_video),
                "-i",
                str(AUDIO_FILE),
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-t",
                str(duration),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-shortest",
                str(OUTPUT_FILE),
            ]
        )


def main():

    print("=" * 70)
    print("SHADOW ARCHIVE — CINEMATIC VIDEO EDITOR V2")
    print("=" * 70)

    if not CLIPS_DIR.exists():
        raise RuntimeError(
            "Video klip klasörü bulunamadı."
        )

    if not AUDIO_FILE.exists():
        raise RuntimeError(
            "Ana video ses dosyası bulunamadı."
        )

    WORK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    duration = get_audio_duration()

    print(
        f"Video süresi: {duration / 60:.2f} dakika"
    )

    segments = create_segments(
        duration
    )

    concat_file = create_concat_file(
        segments
    )

    build_video(
        concat_file,
        duration
    )

    print()
    print("=" * 70)
    print("CINEMATIC V2 TAMAMLANDI")
    print("=" * 70)
    print(
        f"Çıktı: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
