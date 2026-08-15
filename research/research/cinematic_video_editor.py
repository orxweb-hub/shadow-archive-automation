import re
import subprocess
from pathlib import Path


CLIPS_DIR = Path("research/video/clips")

AUDIO_FILE = Path(
    "research/audio/mv_joyita_voice.wav"
)

MUSIC_FILE = Path(
    "research/audio/shorts/mystery_ambient.wav"
)

SUBTITLE_FILE = Path(
    "research/video/subtitles/mv_joyita_english.srt"
)

WORK_DIR = Path(
    "research/video/cinematic_work_v3"
)

OUTPUT_FILE = Path(
    "research/video/shadow_archive_mv_joyita_v3.mp4"
)

ASS_FILE = WORK_DIR / "mv_joyita_english.ass"

WIDTH = 1920
HEIGHT = 1080
FPS = 30


def run(command):

    print(
        "RUN:",
        " ".join(command)
    )

    subprocess.run(
        command,
        check=True
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
            str(AUDIO_FILE),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(
        result.stdout.strip()
    )


def srt_to_seconds(timestamp):

    hours, minutes, rest = timestamp.split(":")

    seconds, milliseconds = rest.split(",")

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000
    )


def ass_time(seconds):

    hours = int(seconds // 3600)

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = (
        seconds
        - hours * 3600
        - minutes * 60
    )

    return (
        f"{hours}:{minutes:02d}:"
        f"{secs:05.2f}"
    )


def parse_srt():

    if not SUBTITLE_FILE.exists():

        raise RuntimeError(
            "İngilizce altyazı dosyası bulunamadı: "
            f"{SUBTITLE_FILE}"
        )

    text = SUBTITLE_FILE.read_text(
        encoding="utf-8"
    )

    blocks = re.split(
        r"\n\s*\n",
        text.strip()
    )

    subtitles = []

    for block in blocks:

        lines = block.splitlines()

        if len(lines) < 3:
            continue

        timing = lines[1]

        if "-->" not in timing:
            continue

        start_text, end_text = (
            timing.split("-->")
        )

        start = srt_to_seconds(
            start_text.strip()
        )

        end = srt_to_seconds(
            end_text.strip()
        )

        subtitle_text = " ".join(
            lines[2:]
        ).strip()

        subtitle_text = (
            subtitle_text
            .replace("&", "&amp;")
            .replace("{", "\\{")
            .replace("}", "\\}")
        )

        if not subtitle_text:
            continue

        subtitles.append(
            (
                start,
                end,
                subtitle_text
            )
        )

    return subtitles


def create_ass_subtitles():

    print(
        "Animasyonlu İngilizce altyazı hazırlanıyor..."
    )

    subtitles = parse_srt()

    if not subtitles:
        raise RuntimeError(
            "SRT içerisinde altyazı bulunamadı."
        )

    ASS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with ASS_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "[Script Info]\n"
        )

        file.write(
            "ScriptType: v4.00+\n"
        )

        file.write(
            "PlayResX: 1920\n"
        )

        file.write(
            "PlayResY: 1080\n"
        )

        file.write(
            "ScaledBorderAndShadow: yes\n\n"
        )

        file.write(
            "[V4+ Styles]\n"
        )

        file.write(
            "Format: "
            "Name, Fontname, Fontsize, "
            "PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, "
            "Encoding\n"
        )

        # Küçük, profesyonel belgesel altyazısı.
        file.write(
            "Style: Default,DejaVu Sans,34,"
            "&H00FFFFFF,&H00FFFFFF,"
            "&H00101010,&H80000000,"
            "1,0,0,0,"
            "100,100,0,0,"
            "1,2,1,"
            "2,80,80,70,"
            "1\n\n"
        )

        file.write(
            "[Events]\n"
        )

        file.write(
            "Format: Layer, Start, End, "
            "Style, Name, MarginL, MarginR, "
            "MarginV, Effect, Text\n"
        )

        for start, end, text in subtitles:

            # Hafif yukarı hareket:
            # 990 -> 955 piksel.
            #
            # Aynı zamanda:
            # fade-in 220 ms
            # fade-out 220 ms

            dialogue = (
                "{\\move(960,990,960,955,0,220)"
                "\\fad(220,220)}"
                f"{text}"
            )

            file.write(
                "Dialogue: 0,"
                f"{ass_time(start)},"
                f"{ass_time(end)},"
                "Default,,0,0,0,,"
                f"{dialogue}\n"
            )

    print(
        f"ASS altyazı hazır: {ASS_FILE}"
    )


def create_segment(
    input_file,
    output_file,
    duration,
    index
):

    if index % 3 == 0:

        zoom = (
            "min(zoom+0.0007,1.10)"
        )

        x = (
            "iw/2-(iw/zoom/2)"
        )

        y = (
            "ih/2-(ih/zoom/2)"
        )

    elif index % 3 == 1:

        zoom = (
            "min(zoom+0.0005,1.08)"
        )

        x = (
            "iw/2-(iw/zoom/2)"
            "+sin(on/18)*25"
        )

        y = (
            "ih/2-(ih/zoom/2)"
        )

    else:

        zoom = (
            "min(zoom+0.0006,1.09)"
        )

        x = (
            "iw/2-(iw/zoom/2)"
        )

        y = (
            "ih/2-(ih/zoom/2)"
            "+sin(on/20)*18"
        )

    fade_in = 0.18

    fade_out_start = max(
        duration - 0.18,
        0
    )

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
        "eq=contrast=1.04:"
        "saturation=0.92:"
        "brightness=-0.015,"
        "vignette=PI/5,"
        f"fade=t=in:st=0:d={fade_in},"
        f"fade=t=out:st={fade_out_start}:d=0.18"
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

    count = (
        int(
            duration /
            segment_duration
        )
        + 1
    )

    segments = []

    for index in range(count):

        clip = clips[
            index % len(clips)
        ]

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

        segments.append(
            output
        )

    return segments


def create_concat_file(
    segments
):

    concat_file = (
        WORK_DIR /
        "concat.txt"
    )

    with concat_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        for segment in segments:

            file.write(
                f"file '{segment.resolve()}'\n"
            )

    return concat_file


def build_base_video(
    concat_file,
    duration
):

    base_video = (
        WORK_DIR /
        "base_video.mp4"
    )

    print(
        "Sinematik görüntü birleştiriliyor..."
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

    return base_video


def add_audio_and_subtitles(
    base_video,
    duration
):

    print(
        "Ses, müzik ve animasyonlu "
        "altyazı ekleniyor..."
    )

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
                audio_filter,

                "-map",
                "0:v",

                "-map",
                "[audio]",

                "-vf",
                f"ass={ASS_FILE}",

                "-t",
                str(duration),

                "-c:v",
                "libx264",

                "-preset",
                "veryfast",

                "-crf",
                "24",

                "-pix_fmt",
                "yuv420p",

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

                "-vf",
                f"ass={ASS_FILE}",

                "-t",
                str(duration),

                "-c:v",
                "libx264",

                "-preset",
                "veryfast",

                "-crf",
                "24",

                "-pix_fmt",
                "yuv420p",

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
    print(
        "SHADOW ARCHIVE — "
        "CINEMATIC VIDEO EDITOR V3"
    )
    print("=" * 70)

    if not CLIPS_DIR.exists():

        raise RuntimeError(
            "Video klip klasörü bulunamadı."
        )

    if not AUDIO_FILE.exists():

        raise RuntimeError(
            "Ana V3 ses dosyası bulunamadı."
        )

    if not SUBTITLE_FILE.exists():

        raise RuntimeError(
            "İngilizce altyazı dosyası bulunamadı."
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
        f"Video süresi: "
        f"{duration / 60:.2f} dakika"
    )

    create_ass_subtitles()

    segments = create_segments(
        duration
    )

    concat_file = create_concat_file(
        segments
    )

    base_video = build_base_video(
        concat_file,
        duration
    )

    add_audio_and_subtitles(
        base_video,
        duration
    )

    print()
    print("=" * 70)
    print(
        "CINEMATIC V3 TAMAMLANDI"
    )
    print("=" * 70)
    print(
        f"Çıktı: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
