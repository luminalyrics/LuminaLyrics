import os
import wave
import struct
import math
import numpy as np
from PIL import Image, ImageDraw

def generate_gradient_image(color1, color2, width, height, output_path):
    """
    Generates a smooth linear gradient image between color1 and color2 (RGB tuples).
    """
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    
    for y in range(height):
        # Calculate interpolation factor
        t = y / (height - 1)
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Draw some abstract circles on top
    draw.ellipse([width//4, height//4, width*3//4, height*3//4], outline=(255,255,255,30), width=3)
    draw.ellipse([width//3, height//3, width*2//3, height*2//3], outline=(255,255,255,20), width=1)
    
    image.save(output_path)
    print(f"Created image: {output_path}")

def generate_kick_sound(duration_sec, sample_rate=22050):
    """
    Generates a synthetic kick drum sound (sine sweep from 150Hz to 40Hz)
    """
    num_samples = int(duration_sec * sample_rate)
    samples = np.zeros(num_samples)
    t = np.arange(num_samples) / sample_rate
    
    # Exponential frequency sweep
    f_start = 150.0
    f_end = 40.0
    k = -15.0 # decay speed
    freqs = f_end + (f_start - f_end) * np.exp(k * t)
    
    # Integrate phase
    phase = 2.0 * np.pi * np.cumsum(freqs) / sample_rate
    samples = np.sin(phase)
    
    # Apply exponential amplitude envelope
    envelope = np.exp(-12.0 * t)
    samples = samples * envelope
    
    return samples

def generate_hihat_sound(duration_sec, sample_rate=22050):
    """
    Generates a synthetic hihat sound (highpass filtered noise)
    """
    num_samples = int(duration_sec * sample_rate)
    # White noise
    noise = np.random.normal(0, 0.4, num_samples)
    t = np.arange(num_samples) / sample_rate
    
    # Envelope
    envelope = np.exp(-40.0 * t)
    return noise * envelope

def generate_synth_note(frequency, duration_sec, sample_rate=22050):
    """
    Generates a synth note (square/sawtooth wave with fade)
    """
    num_samples = int(duration_sec * sample_rate)
    t = np.arange(num_samples) / sample_rate
    # Square wave
    samples = np.sign(np.sin(2.0 * np.pi * frequency * t))
    # Envelope
    envelope = (1.0 - t / duration_sec) * np.exp(-3.0 * t)
    return samples * envelope * 0.15

def generate_test_audio(output_path, duration_sec=16, sample_rate=22050):
    """
    Generates a rhythmic synth track:
    - Kick on beat (0.5s interval -> 120 BPM)
    - Hihat on offbeat (0.25s interval offset)
    - Simple arpeggio melody
    """
    num_samples = int(duration_sec * sample_rate)
    mixed_audio = np.zeros(num_samples)
    
    beat_interval_sec = 0.5 # 120 BPM
    num_beats = int(duration_sec / beat_interval_sec)
    
    # 1. Add Kicks and Hi-Hats
    for b in range(num_beats):
        beat_time = b * beat_interval_sec
        beat_sample = int(beat_time * sample_rate)
        
        # Kick sound (0.3s duration)
        kick = generate_kick_sound(0.3, sample_rate)
        end_idx = min(beat_sample + len(kick), num_samples)
        mixed_audio[beat_sample:end_idx] += kick[:end_idx-beat_sample] * 0.7
        
        # Hi-hat on the off-beat (0.25s after the beat)
        offbeat_sample = beat_sample + int(0.25 * sample_rate)
        if offbeat_sample < num_samples:
            hihat = generate_hihat_sound(0.1, sample_rate)
            end_idx = min(offbeat_sample + len(hihat), num_samples)
            mixed_audio[offbeat_sample:end_idx] += hihat[:end_idx-offbeat_sample] * 0.3
            
    # 2. Add a simple arpeggio melody (C minor)
    notes = [261.63, 311.13, 392.00, 466.16] # C4, Eb4, G4, Bb4
    for b in range(num_beats):
        beat_time = b * beat_interval_sec
        beat_sample = int(beat_time * sample_rate)
        
        note_freq = notes[b % len(notes)]
        note = generate_synth_note(note_freq, 0.45, sample_rate)
        end_idx = min(beat_sample + len(note), num_samples)
        mixed_audio[beat_sample:end_idx] += note[:end_idx-beat_sample] * 0.5
        
    # Normalize to avoid clipping
    max_val = np.max(np.abs(mixed_audio))
    if max_val > 0:
        mixed_audio = mixed_audio / max_val * 0.9
        
    # Write to WAV file
    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for sample in mixed_audio:
            # Scale to 16-bit PCM integer
            val = int(sample * 32767.0)
            data = struct.pack('<h', val)
            wav_file.writeframesraw(data)
            
    print(f"Created test audio: {output_path}")

def main():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Generate Audio
    generate_test_audio(os.path.join(assets_dir, "test_music.wav"))
    
    # 2. Generate Images
    generate_gradient_image((10, 150, 200), (120, 20, 220), 800, 800, os.path.join(assets_dir, "bg_cyan_purple.png"))
    generate_gradient_image((255, 30, 100), (255, 200, 20), 800, 800, os.path.join(assets_dir, "bg_pink_orange.png"))
    generate_gradient_image((20, 50, 240), (20, 200, 100), 800, 800, os.path.join(assets_dir, "bg_blue_green.png"))
    
    # 3. Generate LRC
    lrc_content = """[00:00.00]LuminaLyrics vous souhaite la bienvenue !
[00:03.00]Cette application genere des videos stylisees.
[00:06.00]Le visualiseur reagit a la musique en temps reel.
[00:09.00]Et les images defilent calees sur le rythme.
[00:12.00]Profitez du spectacle !
[00:15.00]
"""
    with open(os.path.join(assets_dir, "test_lyrics.lrc"), "w", encoding="utf-8") as f:
        f.write(lrc_content.strip())
    print("Created lyrics.lrc")
    
    # 4. Generate SRT
    srt_content = """1
00:00:00,000 --> 00:00:03,000
LuminaLyrics vous souhaite la bienvenue !

2
00:00:03,000 --> 00:00:06,000
Cette application genere des videos sous-titrees.

3
00:00:06,000 --> 00:00:09,000
Le visualiseur reagit a la musique en temps reel.

4
00:00:09,000 --> 00:00:12,000
Et les images defilent calees sur le rythme.

5
00:00:12,000 --> 00:00:15,000
Profitez du spectacle !
"""
    with open(os.path.join(assets_dir, "test_lyrics.srt"), "w", encoding="utf-8") as f:
        f.write(srt_content.strip())
    print("Created lyrics.srt")

if __name__ == "__main__":
    main()
