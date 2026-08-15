import numpy as np
import wave
from pathlib import Path

OUTPUT = Path("research/audio/shorts/mystery_ambient.wav")

SAMPLE_RATE = 44100
DURATION = 180

t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)

# Deep cinematic drones
low = 55.0
mid = 82.41

base = (
    0.55 * np.sin(2 * np.pi * low * t)
    + 0.35 * np.sin(2 * np.pi * mid * t)
)

# Slow atmospheric movement
movement = 0.65 + 0.35 * np.sin(2 * np.pi * 0.025 * t)

audio = base * movement

# Add subtle higher atmospheric layer
air = 0.08 * np.sin(2 * np.pi * 164.81 * t)
audio += air

# Normalize strongly enough to be audible
audio = audio / np.max(np.abs(audio))
audio = audio * 0.75

# Fade in/out
fade_time = 8 * SAMPLE_RATE

audio[:fade_time] *= np.linspace(0, 1, fade_time)
audio[-fade_time:] *= np.linspace(1, 0, fade_time)

# Convert to 16-bit PCM
audio_int16 = np.int16(audio * 32767)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with wave.open(str(OUTPUT), "w") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(audio_int16.tobytes())

print(f"Music generated: {OUTPUT}")
