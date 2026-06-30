import sys, os, traceback

run_dir = 'runs/94a55398-e559-4bf6-9ad6-5422f68890fc'
audio_path = os.path.join(run_dir, 'test_music.wav')
lyrics_path = os.path.join(run_dir, 'test_lyrics.lrc')
media_paths = [os.path.join(run_dir, 'bg_blue_green.png')]
output_path = os.path.join(run_dir, 'output_debug.mp4')

print('=== TEST PIPELINE COMPLETE ===', flush=True)

# Step 1: Parse lyrics
from lyrics_parser import parse_lyrics
with open(lyrics_path, 'r', encoding='utf-8') as f:
    content = f.read()
lyrics = parse_lyrics(content, 'test_lyrics.lrc')
print(f'[OK] Lyrics parsed: {len(lyrics)} lines', flush=True)
print(f'  First: {lyrics[0]}', flush=True)

# Step 2: Analyze audio
print('[...] Analyzing audio...', flush=True)
from audio_analyzer import analyze_audio
analysis = analyze_audio(audio_path)
dur = analysis['duration']
bpm = analysis['bpm']
nbeats = len(analysis['beats'])
print(f'[OK] Audio analyzed: duration={dur:.1f}s, bpm={bpm:.1f}, beats={nbeats}', flush=True)

# Step 3: Generate video
print('[...] Generating video...', flush=True)
from video_generator import generate_video

def cb(pct):
    print(f'  Progress: {pct}%', flush=True)

options = {
    'aspect_ratio': '16:9',
    'resolution': '720p',
    'fps': 24,
    'font_family': 'arial',
    'font_size': 48,
    'font_color': '#ffffff',
    'outline_color': '#000000',
    'outline_width': 3,
    'text_position': 'bottom',
    'text_y_offset': 0,
    'visualizer_type': 'bars',
    'visualizer_color': '#00e6ff',
    'bass_zoom_sens': 0.5,
    'bass_flash_sens': 0.3,
    'glitch_sens': 0.2,
    'color_filter': 'none'
}

try:
    generate_video(
        audio_path=audio_path,
        media_paths=media_paths,
        lyrics=lyrics,
        options=options,
        analysis=analysis,
        output_path=output_path,
        progress_callback=cb
    )
    size = os.path.getsize(output_path)
    print(f'[OK] Video generated! Size: {size} bytes', flush=True)
except Exception as e:
    print(f'[FAIL] Error: {e}', flush=True)
    traceback.print_exc()
