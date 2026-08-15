import numpy as np
import wave
from pathlib import Path

OUTPUT = Path("research/audio/shorts/mystery_ambient.wav")

SAMPLE_RATE = 44100
DURATION = 180

t = np.linspace(
    0,
    DURATION,
    int(SAMPLE_RATE * DURATION),
    endpoint=False
)

# --------------------------------------------------
# MASTER ATMOSPHERE
# --------------------------------------------------

audio = np.zeros_like(t)

# --------------------------------------------------
# 1. SOFT DARK PAD
# --------------------------------------------------

pad_freqs = [110.0, 146.83, 164.81]

for freq in pad_freqs:
    slow = 0.65 + 0.35 * np.sin(2 * np.pi * 0.018 * t)
    pad = np.sin(2 * np.pi * freq * t)
    pad += 0.35 * np.sin(2 * np.pi * freq * 2 * t)

    audio += pad * slow * 0.055


# --------------------------------------------------
# 2. DARK PIANO-LIKE NOTES
# --------------------------------------------------

def piano_note(freq, start, length, volume):
    global audio

    start_sample = int(start * SAMPLE_RATE)
    end_sample = min(
        len(audio),
        int((start + length) * SAMPLE_RATE)
    )

    if start_sample >= len(audio):
        return

    local_t = np.arange(end_sample - start_sample) / SAMPLE_RATE

    envelope = np.exp(-3.2 * local_t / length)

    note = (
        np.sin(2 * np.pi * freq * local_t)
        + 0.35 * np.sin(2 * np.pi * freq * 2 * local_t)
        + 0.12 * np.sin(2 * np.pi * freq * 3 * local_t)
    )

    audio[start_sample:end_sample] += (
        note * envelope * volume
    )


# Dark minor progression
notes = [
    (110.00, 0),
    (130.81, 12),
    (146.83, 24),
    (98.00, 36),
    (110.00, 48),
    (130.81, 60),
    (146.83, 72),
    (87.31, 84),
    (110.00, 96),
    (130.81, 108),
    (146.83, 120),
    (98.00, 132),
    (110.00, 144),
    (130.81, 156),
    (87.31, 168),
]

for freq, start in notes:
    piano_note(freq, start, 7.5, 0.13)


# --------------------------------------------------
# 3. HIGH ATMOSPHERIC TONE
# --------------------------------------------------

air_freq = 659.25

air = (
    np.sin(2 * np.pi * air_freq * t)
    + 0.25 * np.sin(2 * np.pi * air_freq * 1.5 * t)
)

air_volume = (
    0.015
    * (0.5 + 0.5 * np.sin(2 * np.pi * 0.011 * t))
)

audio += air * air_volume


# --------------------------------------------------
# 4. VERY LIGHT CINEMATIC PULSES
# --------------------------------------------------

pulse_positions = np.arange(8, DURATION, 8)

for position in pulse_positions:

    start = int(position * SAMPLE_RATE)

    length = int(1.2 * SAMPLE_RATE)

    if start + length >= len(audio):
        continue

    local_t = np.arange(length) / SAMPLE_RATE

    envelope = np.exp(-4.5 * local_t)

    pulse = np.sin(
        2 * np.pi * 73.42 * local_t
    )

    audio[start:start + length] += (
        pulse * envelope * 0.045
    )


# --------------------------------------------------
# 5. SLOW MOVEMENT
# --------------------------------------------------

movement = (
    0.82
    + 0.18 * np.sin(2 * np.pi * 0.008 * t)
)

audio *= movement


# --------------------------------------------------
# NORMALIZE
# --------------------------------------------------

peak = np.max(np.abs(audio))

if peak > 0:
    audio = audio / peak

audio *= 0.62


# --------------------------------------------------
# FADE IN / OUT
# --------------------------------------------------

fade_samples = int(5 * SAMPLE_RATE)

audio[:fade_samples] *= np.linspace(
    0,
    1,
    fade_samples
)

audio[-fade_samples:] *= np.linspace(
    1,
    0,
    fade_samples
)


# --------------------------------------------------
# EXPORT
# --------------------------------------------------

audio_int16 = np.int16(
    np.clip(audio, -1, 1) * 32767
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

with wave.open(str(OUTPUT), "w") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(
        audio_int16.tobytes()
    )

print("==========================================")
print("SHADOW ARCHIVE MYSTERY MUSIC V2")
print("==========================================")
print(f"Output: {OUTPUT}")
print(f"Duration: {DURATION} seconds")
print("Dark piano: ENABLED")
print("Atmosphere: ENABLED")
print("Cinematic pulses: ENABLED")
print("==========================================")
