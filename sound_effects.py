import os
import math
import struct
import wave
import tempfile
import pygame

CHIME_FILE = os.path.join(os.path.dirname(__file__), "wake_chime.wav")

def generate_chime():
    """Генерирует приятный двухтоновый звук активации (динь-дон)"""
    if os.path.exists(CHIME_FILE):
        return CHIME_FILE

    sample_rate = 44100
    # Два коротких тона: 880 Гц (A5) и 1320 Гц (E6)
    tones = [(880, 0.12), (1320, 0.18)]
    audio_data = []

    for freq, duration in tones:
        num_samples = int(sample_rate * duration)
        for i in range(num_samples):
            # Затухание громкости в конце каждого тона
            fade = 1.0 - (i / num_samples)
            sample = math.sin(2 * math.pi * freq * (i / sample_rate)) * fade * 0.4
            int_sample = int(sample * 32767)
            audio_data.append(int_sample)

    with wave.open(CHIME_FILE, "w") as wav_file:
        wav_file.setnchannels(1)  # Моно
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        packed = struct.pack(f"<{len(audio_data)}h", *audio_data)
        wav_file.writeframes(packed)

    return CHIME_FILE

def play_chime():
    """Воспроизводит звук пробуждения"""
    try:
        f = generate_chime()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.Sound(f).play()
    except Exception as e:
        print(f"Ошибка воспроизведения сигнала: {e}")

if __name__ == "__main__":
    generate_chime()
    play_chime()
    import time
    time.sleep(0.5)
