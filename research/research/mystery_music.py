import subprocess
from pathlib import Path

OUTPUT = Path("research/audio/shorts/mystery_ambient.wav")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

duration = 120

filter_complex = (
    "[0:a]volume=0.10,lowpass=f=900,"
    "aecho=0.8:0.88:700:0.25,"
    "afade=t=in:st=0:d=4,"
    f"afade=t=out:st={duration-5}:d=5[a]"
)

cmd = [
    "ffmpeg",
    "-y",
    "-f",
    "lavfi",
    "-i",
    "sine=frequency=55:duration=120",
    "-f",
    "lavfi",
    "-i",
    "sine=frequency=82.41:duration=120",
    "-filter_complex",
    (
        "[0:a][1:a]amix=inputs=2:duration=longest,"
        "volume=0.12,"
        "lowpass=f=700,"
        "aecho=0.8:0.9:800:0.25,"
        "afade=t=in:st=0:d=5,"
        "afade=t=out:st=115:d=5"
    ),
    "-ac",
    "2",
    "-ar",
    "44100",
    str(OUTPUT)
]

print("Gizemli atmosfer müziği oluşturuluyor...")

subprocess.run(
    cmd,
    check=True
)

print(f"Hazır: {OUTPUT}")
