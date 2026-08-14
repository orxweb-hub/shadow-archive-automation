import json
import subprocess
from pathlib import Path


VIDEO_DIR = Path("research/video")
CLIPS_DIR = VIDEO_DIR / "clips"
ASSETS_FILE = VIDEO_DIR / "visual_assets.json"

AUDIO_FILE = Path("research/audio/mv_joyita_voice.wav")
OUTPUT_FILE = VIDEO_DIR / "shadow_archive_mv_joyita.mp4"

WIDTH = 1920
HEIGHT = 1080


def run(command):
    print(">", " ".join(str(x) for x in command))

    result = subprocess.run(
        command,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Komut başarısız oldu."
        )


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
            str(AUDIO_FILE)
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Ses süresi okunamadı."
        )

    return float(result.stdout.strip())


def create_clip_list(audio_duration):

    assets = json.loads(
        ASSETS_FILE.read_text(
            encoding="utf-8"
        )
    )

    assets = [
        item for item in assets
        if Path(item["file"]).exists()
    ]

    if not assets:
        raise RuntimeError(
            "Hiç görüntü bulunamadı."
        )

    # Görüntüleri tekrar kullanarak
    # toplam ses süresini dolduruyoruz.
    selected = []

    current = 0.0
    index = 0

    while current < audio_duration:

        asset = assets[index % len(assets)]

        duration = min(
            float(asset.get("duration_hint", 20)),
            audio_duration - current
        )

        selected.append({
            "file": asset["file"],
            "duration": duration
        })

        current += duration
        index += 1

    return selected


def create_video_segment(input_file, output_file, duration):

    # Hafif sinematik zoom.
    # Görüntüyü basit slideshow gibi göstermemek için
    # sürekli çok yavaş bir hareket uygulanıyor.

    filter_complex = (
        f"scale={WIDTH}:{HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        "zoompan="
        "z='min(zoom+0.0007,1.08)':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1920x1080:"
        "fps=30,"
        "setsar=1"
    )

    run([
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(input_file),
        "-t",
        str(duration),
        "-vf",
        filter_complex,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "21",
        "-pix_fmt",
        "yuv420p",
        str(output_file)
    ])


def create_concat_file(segments):

    concat_file = VIDEO_DIR / "concat.txt"

    with concat_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        for segment in segments:

            path = Path(
                segment["output"]
            ).resolve()

            file.write(
                f"file '{path}'\n"
            )

    return concat_file


def concatenate_segments(
    concat_file,
    output_video
):

    run([
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
        str(output_video)
    ])


def add_audio(video_file):

    final_file = OUTPUT_FILE

    run([
        "ffmpeg",
        "-y",
        "-i",
        str(video_file),
        "-i",
        str(AUDIO_FILE),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(final_file)
    ])

    return final_file


def main():

    print()
    print("=" * 60)
    print("SHADOW ARCHIVE — VIDEO EDITOR")
    print("=" * 60)

    if not AUDIO_FILE.exists():
        raise FileNotFoundError(
            f"Ses bulunamadı: {AUDIO_FILE}"
        )

    if not ASSETS_FILE.exists():
        raise FileNotFoundError(
            f"Görsel listesi bulunamadı: {ASSETS_FILE}"
        )

    VIDEO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    segments_dir = VIDEO_DIR / "segments"

    segments_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    audio_duration = get_audio_duration()

    print(
        f"Ses süresi: {audio_duration / 60:.2f} dakika"
    )

    clips = create_clip_list(
        audio_duration
    )

    print(
        f"Oluşturulacak sahne sayısı: {len(clips)}"
    )

    segments = []

    for number, clip in enumerate(
        clips,
        start=1
    ):

        output = (
            segments_dir /
            f"segment_{number:04d}.mp4"
        )

        print(
            f"[{number}/{len(clips)}] "
            f"Video hazırlanıyor..."
        )

        create_video_segment(
            clip["file"],
            output,
            clip["duration"]
        )

        segments.append({
            "output": str(output)
        })

    concat_file = create_concat_file(
        segments
    )

    silent_video = VIDEO_DIR / "silent_video.mp4"

    print("Sahneler birleştiriliyor...")

    concatenate_segments(
        concat_file,
        silent_video
    )

    print("Ses ekleniyor...")

    final_file = add_audio(
        silent_video
    )

    print()
    print("=" * 60)
    print("VIDEO HAZIR")
    print("=" * 60)
    print(f"Dosya: {final_file}")


if __name__ == "__main__":
    main()
