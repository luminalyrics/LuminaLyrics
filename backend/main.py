import os
import uuid
import json
import shutil
import threading
import traceback
import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from audio_analyzer import analyze_audio
from lyrics_parser import parse_lyrics
from video_generator import generate_video

# ── Version banner ──────────────────────────────────────────────────────────
VERSION = "v3.0 - 2026-06-29"
print(f"\n{'='*60}")
print(f"  LuminaLyrics Backend  {VERSION}")
print(f"  Python threading-based pipeline")
print(f"{'='*60}\n", flush=True)

app = FastAPI(title="LuminaLyrics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks_db: dict = {}
tasks_lock = threading.Lock()

RUNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
os.makedirs(RUNS_DIR, exist_ok=True)


# ── Per-task log helper ──────────────────────────────────────────────────────
def task_log(task_dir: str, task_id: str, msg: str):
    """Write a timestamped message to the task's log file and stdout."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(f"[TASK {task_id[:8]}] {line}", flush=True)
    try:
        with open(os.path.join(task_dir, "task.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Pipeline ────────────────────────────────────────────────────────────────
def run_pipeline(task_id: str, audio_filename: str, media_filenames: List[str],
                 lyrics_filename: str, options_dict: dict, font_filename: Optional[str] = None):

    task_dir = os.path.join(RUNS_DIR, task_id)
    log = lambda msg: task_log(task_dir, task_id, msg)

    # !! This is the VERY FIRST thing the thread does !!
    log(f"Thread started. audio={audio_filename} lyrics={lyrics_filename} media={media_filenames}")

    try:
        audio_path   = os.path.join(task_dir, audio_filename)
        lyrics_path  = os.path.join(task_dir, lyrics_filename)
        media_paths  = [os.path.join(task_dir, n) for n in media_filenames]
        output_path  = os.path.join(task_dir, "output.mp4")

        # Inject the task directory so the generator can resolve the custom font
        options_dict["task_dir"] = task_dir

        # Sanity checks
        for p in [audio_path, lyrics_path] + media_paths:
            if not os.path.exists(p):
                raise FileNotFoundError(f"File not found: {p}")
            log(f"File OK: {os.path.basename(p)} ({os.path.getsize(p)} bytes)")

        # ── STATUS: analyzing ───────────────────────────────────────────────
        with tasks_lock:
            tasks_db[task_id]["status"]   = "analyzing"
            tasks_db[task_id]["progress"] = 5
        log("Status → analyzing (5%)")

        # Parse lyrics
        with open(lyrics_path, "r", encoding="utf-8", errors="ignore") as f:
            lyrics_content = f.read()
        lyrics = parse_lyrics(lyrics_content, lyrics_filename)
        if not lyrics:
            raise ValueError("Aucune parole trouvée. Vérifiez le format (.lrc ou .srt) et les balises temporelles.")
        log(f"Lyrics parsed: {len(lyrics)} lines")

        # Analyze audio
        log("Starting audio analysis (FFmpeg conversion + beat detection)…")
        analysis = analyze_audio(audio_path)
        log(f"Audio analyzed: duration={analysis['duration']:.1f}s  bpm={analysis['bpm']:.1f}  beats={len(analysis['beats'])}")

        if analysis["duration"] <= 0:
            raise ValueError(f"Durée audio invalide: {analysis['duration']}s. Fichier audio corrompu ?")

        # ── STATUS: rendering ───────────────────────────────────────────────
        with tasks_lock:
            tasks_db[task_id]["status"]   = "rendering"
            tasks_db[task_id]["progress"] = 15
        log("Status → rendering (15%)")

        def progress_callback(pct: int):
            scaled = 15 + int(pct * 0.83)
            with tasks_lock:
                tasks_db[task_id]["progress"] = scaled
            if pct % 10 == 0:
                log(f"Render progress: {pct}% → scaled {scaled}%")

        # Generate video
        log("Starting video generation…")
        generate_video(
            audio_path=audio_path,
            media_paths=media_paths,
            lyrics=lyrics,
            options=options_dict,
            analysis=analysis,
            output_path=output_path,
            progress_callback=progress_callback,
        )

        size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        log(f"Video generated: {size} bytes ({size // 1024} KB)")

        with tasks_lock:
            tasks_db[task_id]["status"]    = "completed"
            tasks_db[task_id]["progress"]  = 100
            tasks_db[task_id]["video_url"] = f"/api/download/{task_id}"
        log("Status → completed ✓")

    except Exception as e:
        err = str(e)
        log(f"FAILED: {err}")
        log(traceback.format_exc())
        with tasks_lock:
            tasks_db[task_id]["status"] = "failed"
            tasks_db[task_id]["error"]  = err


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": VERSION, "active_tasks": len(tasks_db)}


@app.get("/api/tasks")
async def list_tasks():
    """Debug endpoint – shows all tasks and their current status."""
    with tasks_lock:
        return {k: dict(v) for k, v in tasks_db.items()}


@app.post("/api/generate")
async def generate_lyrics_video(
    audio:   UploadFile = File(...),
    lyrics:  UploadFile = File(...),
    media:   List[UploadFile] = File(...),
    options: str = Form(...),
    font:    Optional[UploadFile] = File(None),
):
    try:
        options_dict = json.loads(options)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid options JSON")

    task_id  = str(uuid.uuid4())
    task_dir = os.path.join(RUNS_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    audio_filename = audio.filename or "audio.mp3"
    with open(os.path.join(task_dir, audio_filename), "wb") as buf:
        shutil.copyfileobj(audio.file, buf)

    lyrics_filename = lyrics.filename or "lyrics.lrc"
    with open(os.path.join(task_dir, lyrics_filename), "wb") as buf:
        shutil.copyfileobj(lyrics.file, buf)

    media_filenames = []
    for f in media:
        fname = f.filename or f"media_{len(media_filenames)}.jpg"
        with open(os.path.join(task_dir, fname), "wb") as buf:
            shutil.copyfileobj(f.file, buf)
        media_filenames.append(fname)

    # Optional custom font
    font_filename = None
    if font and font.filename:
        font_filename = font.filename
        with open(os.path.join(task_dir, font_filename), "wb") as buf:
            shutil.copyfileobj(font.file, buf)
        options_dict["custom_font_filename"] = font_filename
        print(f"  font    = {font_filename}", flush=True)

    with tasks_lock:
        tasks_db[task_id] = {"status": "queued", "progress": 0, "error": None, "video_url": None}

    print(f"\n[NEW TASK] {task_id}", flush=True)
    print(f"  audio   = {audio_filename}", flush=True)
    print(f"  lyrics  = {lyrics_filename}", flush=True)
    print(f"  media   = {media_filenames}", flush=True)

    t = threading.Thread(
        target=run_pipeline,
        kwargs={
            "task_id":         task_id,
            "audio_filename":  audio_filename,
            "media_filenames": media_filenames,
            "lyrics_filename": lyrics_filename,
            "options_dict":    options_dict,
            "font_filename":   font_filename,
        },
        daemon=True,
        name=f"pipeline-{task_id[:8]}",
    )
    t.start()
    print(f"  thread  = {t.name} (alive={t.is_alive()})", flush=True)

    return {"task_id": task_id}


@app.get("/api/status/{task_id}")
async def get_status(task_id: str, response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    with tasks_lock:
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(tasks_db[task_id])


@app.get("/api/log/{task_id}")
async def get_task_log(task_id: str):
    """Returns the task's log file content for debugging."""
    task_dir = os.path.join(RUNS_DIR, task_id)
    log_path = os.path.join(task_dir, "task.log")
    if not os.path.exists(log_path):
        return {"log": "(no log file yet — task may not have started)"}
    with open(log_path, "r", encoding="utf-8") as f:
        return {"log": f.read()}


@app.get("/api/download/{task_id}")
async def download_video(task_id: str):
    output_path = os.path.join(RUNS_DIR, task_id, "output.mp4")
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Video not ready")
    return FileResponse(path=output_path, media_type="video/mp4",
                        filename=f"lyrics_video_{task_id[:8]}.mp4")
@app.delete("/api/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """Deletes the task directory and its contents to free up space."""
    task_dir = os.path.join(RUNS_DIR, task_id)
    if os.path.exists(task_dir):
        shutil.rmtree(task_dir, ignore_errors=True)
    
    with tasks_lock:
        if task_id in tasks_db:
            del tasks_db[task_id]
            
    return {"status": "cleaned", "task_id": task_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
