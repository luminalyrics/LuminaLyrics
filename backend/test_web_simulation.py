"""
Simulates EXACTLY what the web frontend does:
- Audio: MP3 file (real user upload format)
- Image: JPEG/PNG (real user upload)
- Goes through run_pipeline (same code as web server)
"""
import sys, os, threading, time

# Bootstrap the same environment as main.py
sys.path.insert(0, '.')

from main import run_pipeline, tasks_db, tasks_lock

# Use the MP3 file (real upload scenario)
import shutil, uuid

task_id = str(uuid.uuid4())
task_dir = os.path.join('runs', task_id)
os.makedirs(task_dir, exist_ok=True)

# Copy files as if they were uploaded
audio_filename = 'test_real_upload.mp3'
lyrics_filename = 'test_lyrics.lrc'
media_filename  = 'bg_blue_green.png'

shutil.copy('test_real_upload.mp3', os.path.join(task_dir, audio_filename))
shutil.copy('runs/94a55398-e559-4bf6-9ad6-5422f68890fc/test_lyrics.lrc', os.path.join(task_dir, lyrics_filename))
shutil.copy('runs/94a55398-e559-4bf6-9ad6-5422f68890fc/bg_blue_green.png', os.path.join(task_dir, media_filename))

# Init task
with tasks_lock:
    tasks_db[task_id] = {'status': 'queued', 'progress': 0, 'error': None, 'video_url': None}

options_dict = {
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

print(f'[TEST] Task: {task_id}', flush=True)
print(f'[TEST] Audio: {audio_filename}', flush=True)
print(f'[TEST] Running via run_pipeline (same as web server)...', flush=True)

# Run via thread (same as web server)
t = threading.Thread(
    target=run_pipeline,
    kwargs={
        'task_id': task_id,
        'audio_filename': audio_filename,
        'media_filenames': [media_filename],
        'lyrics_filename': lyrics_filename,
        'options_dict': options_dict
    },
    daemon=False
)
t.start()

# Poll status
prev_status = None
while t.is_alive():
    with tasks_lock:
        s = dict(tasks_db[task_id])
    if s['status'] != prev_status or s.get('progress', 0) % 10 == 0:
        print(f'  Status: {s["status"]} | Progress: {s.get("progress",0)}%', flush=True)
        prev_status = s['status']
    time.sleep(1)

t.join()

with tasks_lock:
    final = dict(tasks_db[task_id])

print(f'\n[RESULT] Status: {final["status"]}', flush=True)
print(f'[RESULT] Progress: {final["progress"]}%', flush=True)
if final['error']:
    print(f'[RESULT] Error: {final["error"]}', flush=True)

output_path = os.path.join(task_dir, 'output.mp4')
if os.path.exists(output_path):
    size = os.path.getsize(output_path)
    print(f'[RESULT] output.mp4 size: {size} bytes ({size//1024} KB)', flush=True)
    if size < 10000:
        print('[RESULT] !! FILE IS TOO SMALL - VIDEO IS EMPTY !!', flush=True)
    else:
        print('[RESULT] Video looks good!', flush=True)
else:
    print('[RESULT] No output.mp4 created!', flush=True)
