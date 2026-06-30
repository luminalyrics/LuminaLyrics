import os
import re
import cv2
import numpy as np
import subprocess
import threading
from PIL import Image, ImageDraw, ImageFont

def get_font(font_family: str, size: int, custom_font_path: str = None):
    """
    Loads a TrueType font on Windows or falls back to default.
    If custom_font_path is provided, it takes priority over the system font map.
    """
    # 1. Try the uploaded custom font first
    if custom_font_path and os.path.exists(custom_font_path):
        try:
            return ImageFont.truetype(custom_font_path, size)
        except Exception:
            pass  # Fall through to system fonts

    # Map friendly names to Windows system font paths
    font_map = {
        "arial": "C:\\Windows\\Fonts\\arial.ttf",
        "arialbd": "C:\\Windows\\Fonts\\arialbd.ttf",
        "courier": "C:\\Windows\\Fonts\\cour.ttf",
        "georgia": "C:\\Windows\\Fonts\\georgia.ttf",
        "impact": "C:\\Windows\\Fonts\\impact.ttf",
        "times": "C:\\Windows\\Fonts\\times.ttf",
        "verdana": "C:\\Windows\\Fonts\\verdana.ttf"
    }
    
    font_path = font_map.get(font_family.lower(), "C:\\Windows\\Fonts\\arial.ttf")
    
    if not os.path.exists(font_path):
        # Search Windows font directory for any ttf
        win_fonts_dir = "C:\\Windows\\Fonts"
        if os.path.exists(win_fonts_dir):
            for file in os.listdir(win_fonts_dir):
                if file.lower().endswith(".ttf"):
                    font_path = os.path.join(win_fonts_dir, file)
                    break
        else:
            font_path = None
            
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
        
    return ImageFont.load_default()

def hex_to_bgr(hex_str: str) -> tuple:
    """
    Converts '#RRGGBB' to BGR tuple (0-255).
    """
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return (255, 255, 255) # default white
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (b, g, r)

def hex_to_rgb(hex_str: str) -> tuple:
    """
    Converts '#RRGGBB' to RGB tuple (0-255).
    """
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return (255, 255, 255)
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (r, g, b)

def crop_to_fill(frame: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """
    Resizes and crops a frame so that it covers the target_w x target_h area.
    Similar to CSS background-size: cover.
    """
    h, w = frame.shape[:2]
    
    scale_x = target_w / w
    scale_y = target_h / h
    scale = max(scale_x, scale_y)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # Crop to center
    start_x = (new_w - target_w) // 2
    start_y = (new_h - target_h) // 2
    
    cropped = resized[start_y:start_y+target_h, start_x:start_x+target_w]
    return cropped

class MediaManager:
    """
    Manages loading and reading of uploaded image and video assets.
    """
    def __init__(self, media_paths: list, target_w: int, target_h: int):
        self.media_paths = [p for p in media_paths if os.path.exists(p)]
        self.target_w = target_w
        self.target_h = target_h
        
        # Keep track of open videos to avoid opening/closing them constantly
        self.caps = {}
        self.current_idx = -1
        
    def get_frame(self, media_idx: int, frame_time: float) -> np.ndarray:
        """
        Retrieves a cropped frame from the media corresponding to media_idx.
        If it's an image, returns the resized image.
        If it's a video, reads the frame corresponding to the current time.
        """
        if not self.media_paths:
            # Return dark blue gradient placeholder if no media
            img = np.zeros((self.target_h, self.target_w, 3), dtype=np.uint8)
            cv2.putText(img, "Pas de media", (50, self.target_h // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            return img
            
        idx = media_idx % len(self.media_paths)
        path = self.media_paths[idx]
        ext = path.lower().split('.')[-1]
        
        # Check if image
        if ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp']:
            img = cv2.imread(path)
            if img is None:
                img = np.zeros((self.target_h, self.target_w, 3), dtype=np.uint8)
            return crop_to_fill(img, self.target_w, self.target_h)
            
        # Video handling
        else:
            if idx not in self.caps:
                self.caps[idx] = cv2.VideoCapture(path)
                
            cap = self.caps[idx]
            
            # Read next frame
            ret, frame = cap.read()
            if not ret:
                # Loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                
            if ret and frame is not None:
                return crop_to_fill(frame, self.target_w, self.target_h)
            else:
                # Return empty frame on failure
                return np.zeros((self.target_h, self.target_w, 3), dtype=np.uint8)

    def close(self):
        """Closes all open VideoCaptures."""
        for cap in self.caps.values():
            cap.release()
        self.caps.clear()

def apply_color_filter(frame: np.ndarray, filter_name: str) -> np.ndarray:
    """
    Applies simple color filters to a BGR frame.
    """
    filter_name = filter_name.lower()
    if filter_name == 'grayscale':
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
    elif filter_name == 'sepia':
        # Sepia kernel
        kernel = np.array([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ])
        return cv2.transform(frame, kernel)
        
    elif filter_name == 'cool':
        # Boost blue and green, reduce red
        frame_cool = frame.copy().astype(np.float32)
        frame_cool[:, :, 0] = np.clip(frame_cool[:, :, 0] * 1.15, 0, 255) # Blue
        frame_cool[:, :, 1] = np.clip(frame_cool[:, :, 1] * 1.05, 0, 255) # Green
        frame_cool[:, :, 2] = np.clip(frame_cool[:, :, 2] * 0.85, 0, 255) # Red
        return frame_cool.astype(np.uint8)
        
    elif filter_name == 'warm':
        # Boost red and yellow (red + green)
        frame_warm = frame.copy().astype(np.float32)
        frame_warm[:, :, 0] = np.clip(frame_warm[:, :, 0] * 0.85, 0, 255) # Blue
        frame_warm[:, :, 1] = np.clip(frame_warm[:, :, 1] * 1.05, 0, 255) # Green
        frame_warm[:, :, 2] = np.clip(frame_warm[:, :, 2] * 1.20, 0, 255) # Red
        return frame_warm.astype(np.uint8)
        
    return frame

def draw_visualizer(frame: np.ndarray, fft_row: np.ndarray, visualizer_type: str, color_hex: str, target_w: int, target_h: int):
    """
    Draws audio visualizer on the frame.
    """
    if visualizer_type == 'none' or fft_row is None:
        return
        
    color_bgr = hex_to_bgr(color_hex)
    num_bins = len(fft_row)
    
    if visualizer_type == 'bars':
        # Draw vertical spectrum bars at the bottom
        bar_w = int(target_w / num_bins)
        margin = 2
        max_height = int(target_h * 0.25) # Max 25% of height
        
        for idx, val in enumerate(fft_row):
            # Val is between 0 and 1
            bar_h = int(val * max_height)
            x_start = idx * bar_w + margin
            x_end = (idx + 1) * bar_w - margin
            y_start = target_h - 10 - bar_h
            y_end = target_h - 10
            
            if bar_h > 0:
                cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), color_bgr, -1)
                
    elif visualizer_type == 'waveform':
        # Draw a squiggly line representing the soundwave at the bottom third
        y_center = int(target_h * 0.75)
        points = []
        step = target_w / (num_bins - 1)
        max_amp = int(target_h * 0.1)
        
        # Mirror the bins to make it look like a symmetric wave
        for idx in range(num_bins):
            # Use alternating signs to make a wave-like look, scaled by FFT bin
            sign = 1 if idx % 2 == 0 else -1
            val = fft_row[idx]
            x = int(idx * step)
            y = int(y_center + sign * val * max_amp)
            points.append([x, y])
            
        points = np.array(points, dtype=np.int32)
        cv2.polylines(frame, [points], False, color_bgr, 3, lineType=cv2.LINE_AA)
        
    elif visualizer_type == 'circle':
        # Draw a circle in the center, with spikes radiating outward based on FFT values
        center_x = target_w // 2
        center_y = target_h // 2
        
        # Base circle radius is 10% of height, with extra growth from bass bin (idx 0)
        base_radius = int(target_h * 0.1)
        bass_boost = int(fft_row[0] * target_h * 0.05)
        radius = base_radius + bass_boost
        
        # Draw central circle
        cv2.circle(frame, (center_x, center_y), radius, color_bgr, 2, lineType=cv2.LINE_AA)
        
        # Radiate lines outward
        num_spikes = 64
        angle_step = 2 * np.pi / num_spikes
        max_spike_len = int(target_h * 0.12)
        
        for idx in range(num_spikes):
            angle = idx * angle_step
            # Map index to fft_row (cycle through 32 bins)
            fft_idx = idx % num_bins
            val = fft_row[fft_idx]
            
            spike_len = int(val * max_spike_len)
            
            x_start = int(center_x + radius * np.cos(angle))
            y_start = int(center_y + radius * np.sin(angle))
            
            x_end = int(center_x + (radius + spike_len) * np.cos(angle))
            y_end = int(center_y + (radius + spike_len) * np.sin(angle))
            
            if spike_len > 0:
                cv2.line(frame, (x_start, y_start), (x_end, y_end), color_bgr, 2, lineType=cv2.LINE_AA)

def wrap_text_to_lines(text: str, font, draw, max_width: int) -> list:
    """
    Wraps text into as many lines as needed so each line fits within max_width.
    Uses a greedy algorithm based on real pixel widths (not character count).
    Returns a list of strings.
    """
    words = text.split()
    if not words:
        return [text]

    lines = []
    current_line = ""

    for word in words:
        test_line = (current_line + " " + word).strip()
        lb = draw.textbbox((0, 0), test_line, font=font)
        if lb[2] - lb[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


def draw_lyrics_pil(frame: np.ndarray, active_lyric: dict, frame_time: float, font_family: str, font_size: int, font_color_hex: str, outline_color_hex: str, outline_width: int, position: str, y_offset: float, target_w: int, target_h: int, karaoke_effect: bool = True, custom_font_path: str = None) -> np.ndarray:
    """
    Renders text with a karaoke progressive highlight using PIL.
    Automatically wraps long lines and shrinks the font if individual words
    still exceed 80% of the frame width (e.g. TikTok 9:16 format).
    """
    if not active_lyric:
        return frame

    text = active_lyric["text"]
    start = active_lyric["start"]
    end = active_lyric["end"]
    duration = end - start

    # Calculate progress of the current lyric line (0.0 → 1.0)
    progress = 0.0
    if duration > 0:
        progress = max(0.0, min(1.0, (frame_time - start) / duration))

    # Convert OpenCV frame (BGR) to PIL Image (RGB)
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    # ── Font size: auto-shrink until every word fits within max_text_width ──
    max_text_width = int(target_w * 0.80)  # 80% of frame width
    min_font_size = max(12, int(font_size * 0.60))  # never go below 60% of original
    current_font_size = font_size

    while current_font_size > min_font_size:
        font = get_font(font_family, current_font_size, custom_font_path)
        # Check if the longest single word already overflows
        words = text.split()
        longest_word_w = max(
            (draw.textbbox((0, 0), w, font=font)[2] - draw.textbbox((0, 0), w, font=font)[0])
            for w in words
        ) if words else 0
        if longest_word_w <= max_text_width:
            break
        current_font_size -= 2

    font = get_font(font_family, current_font_size, custom_font_path)

    # ── Word-wrap: greedy split based on real pixel widths ───────────────────
    lines = wrap_text_to_lines(text, font, draw, max_text_width)

    # Measure each line
    line_metrics = []
    for line in lines:
        lb = draw.textbbox((0, 0), line, font=font)
        line_metrics.append({
            "text": line,
            "w": lb[2] - lb[0],
            "h": lb[3] - lb[1],
        })

    line_h = line_metrics[0]["h"]
    line_spacing = int(line_h * 0.25)  # 25% extra gap between lines
    total_block_h = len(lines) * line_h + (len(lines) - 1) * line_spacing

    # Vertical anchor of the text block
    if position == 'top':
        block_y = int(target_h * 0.15 + y_offset)
    elif position == 'middle':
        block_y = int((target_h - total_block_h) // 2 + y_offset)
    else:  # bottom
        block_y = int(target_h * 0.80 - total_block_h + y_offset)

    font_color_rgb = hex_to_rgb(font_color_hex)
    outline_color_rgb = hex_to_rgb(outline_color_hex)
    highlight_color_rgb = (255, 235, 59)  # bright yellow/gold

    # Total character count across all lines (for progress mapping)
    total_chars = sum(len(m["text"]) for m in line_metrics)
    chars_done_global = int(progress * total_chars)

    # Helper to draw text with outline
    def draw_text_with_outline(draw_obj, t_x, t_y, t_text, t_font, fill_color, out_color, out_width):
        if out_width > 0:
            for dx in range(-out_width, out_width + 1):
                for dy in range(-out_width, out_width + 1):
                    if dx != 0 or dy != 0:
                        draw_obj.text((t_x + dx, t_y + dy), t_text, font=t_font, fill=out_color)
        draw_obj.text((t_x, t_y), t_text, font=t_font, fill=fill_color)

    # Create highlight overlay once (shared across all lines)
    hl_img = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    hl_draw = ImageDraw.Draw(hl_img)

    chars_seen = 0  # character counter across lines

    for i, metric in enumerate(line_metrics):
        line_text = metric["text"]
        lw = metric["w"]
        x = (target_w - lw) // 2
        y = block_y + i * (line_h + line_spacing)

        # 1. Draw base text (full line, normal color)
        draw_text_with_outline(draw, x, y, line_text, font, font_color_rgb, outline_color_rgb, outline_width)

        if karaoke_effect:
            # 2. Draw highlight text on transparent overlay (full line)
            draw_text_with_outline(hl_draw, x, y, line_text, font, highlight_color_rgb, outline_color_rgb, outline_width)

            # 3. Determine how many chars of this line are highlighted
            line_char_count = len(line_text)
            chars_in_this_line = max(0, min(line_char_count, chars_done_global - chars_seen))
            chars_seen += line_char_count

            if chars_in_this_line > 0 and progress > 0:
                # Measure pixel width of the highlighted portion
                highlighted_text = line_text[:chars_in_this_line]
                hl_lb = draw.textbbox((0, 0), highlighted_text, font=font)
                hl_w = hl_lb[2] - hl_lb[0]

                crop_box = (x, y - outline_width, x + hl_w, y + line_h + outline_width)
                hl_cropped = hl_img.crop(crop_box)
                img_pil.paste(hl_cropped, (x, y - outline_width), hl_cropped)

    # Convert back to BGR OpenCV array
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def apply_glitch(frame: np.ndarray, intensity: float) -> np.ndarray:
    """
    Applies a cool RGB split and pixel offset glitch to the frame.
    """
    h, w = frame.shape[:2]
    glitched = frame.copy()
    
    # RGB split: offset channels horizontally
    shift = int(intensity * 15)
    if shift > 0:
        # Red channel shift
        glitched[:, shift:, 2] = frame[:, :-shift, 2]
        # Blue channel shift in opposite direction
        glitched[:, :-shift, 0] = frame[:, shift:, 0]
        
    # Horizontal slice offset
    num_slices = int(intensity * 5)
    for _ in range(num_slices):
        slice_y = np.random.randint(0, h - 20)
        slice_h = np.random.randint(5, 20)
        slice_shift = np.random.randint(-shift * 2, shift * 2 + 1)
        
        if slice_shift != 0:
            # Shift slice of frame horizontally
            slide_slice = glitched[slice_y:slice_y+slice_h, :]
            glitched[slice_y:slice_y+slice_h, :] = np.roll(slide_slice, slice_shift, axis=1)
            
    return glitched

def generate_video(audio_path: str, media_paths: list, lyrics: list, options: dict, analysis: dict, output_path: str, progress_callback=None):
    """
    Compiles the final MP4 video using the frames generation loop and ffmpeg pipe.
    """
    # 1. Resolve resolution & aspect ratio
    aspect = options.get("aspect_ratio", "16:9")
    resolution = options.get("resolution", "720p")
    fps = int(options.get("fps", 30))
    
    res_map = {
        "16:9": {"1080p": (1920, 1080), "720p": (1280, 720)},
        "9:16": {"1080p": (1080, 1920), "720p": (720, 1280)},
        "1:1": {"1080p": (1080, 1080), "720p": (720, 720)}
    }
    
    target_w, target_h = res_map.get(aspect, res_map["16:9"]).get(resolution, (1280, 720))
    
    # 2. Setup video parameters
    duration = analysis["duration"]
    total_frames = int(duration * fps)
    
    # Beats configuration: Switch media every 4 beats
    beats = analysis["beats"]
    beats_np = np.array(beats)
    
    # Media Manager
    media_mgr = MediaManager(media_paths, target_w, target_h)
    
    # ffmpeg output command - pipe raw BGR frames to ffmpeg stdin
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{target_w}x{target_h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",        # video from stdin
        "-i", audio_path, # audio from file
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        # libvo_aacenc is required for this FFmpeg version (pre-2014)
        # For newer FFmpeg, use: "-c:a", "aac", "-strict", "-2"
        "-c:a", "libvo_aacenc",
        "-b:a", "128k",
        "-shortest",
        output_path
    ]

    # Drain stderr in a background thread to avoid pipe deadlock
    # (if stderr buffer fills up, ffmpeg blocks waiting for us to read it)
    stderr_lines = []
    def _drain_stderr(proc):
        for line in proc.stderr:
            decoded = line.decode('utf-8', errors='ignore').rstrip()
            if decoded:
                stderr_lines.append(decoded)
                print(f"[ffmpeg] {decoded}", flush=True)

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    stderr_thread = threading.Thread(target=_drain_stderr, args=(process,), daemon=True)
    stderr_thread.start()
    
    # Retrieve options
    font_family = options.get("font_family", "arial")
    font_size = int(options.get("font_size", 40))
    font_color = options.get("font_color", "#ffffff")
    outline_color = options.get("outline_color", "#000000")
    outline_width = int(options.get("outline_width", 3))
    karaoke_effect = bool(options.get("karaoke_effect", True))
    text_position = options.get("text_position", "bottom")
    text_y_offset = float(options.get("text_y_offset", 0.0))
    
    visualizer_type = options.get("visualizer_type", "bars")
    visualizer_color = options.get("visualizer_color", "#ff00ff")
    
    bass_zoom_sens = float(options.get("bass_zoom_sens", 0.5))
    bass_flash_sens = float(options.get("bass_flash_sens", 0.3))
    glitch_sens = float(options.get("glitch_sens", 0.2))
    glitch_intensity_factor = float(options.get("glitch_intensity", 1.0))
    color_filter = options.get("color_filter", "none")
    
    # Custom font path (from uploaded file)
    task_dir = options.get("task_dir", "")
    custom_font_filename = options.get("custom_font_filename", "")
    custom_font_path = os.path.join(task_dir, custom_font_filename) if task_dir and custom_font_filename else None

    # Cache time axis & envelopes
    time_axis = analysis["time_axis"]
    bass_envelope = analysis["bass_envelope"]
    rms_envelope = analysis["rms_envelope"]
    fft_data = analysis["fft_data"]
    
    white_overlay = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
    
    try:
        for f_idx in range(total_frames):
            frame_time = f_idx / fps
            
            # A. Select current media index based on beats
            # Find how many beats have passed
            beat_idx = np.searchsorted(beats_np, frame_time)
            # Switch media every 4 beats
            media_idx = beat_idx // 4
            
            # Get frame
            frame = media_mgr.get_frame(media_idx, frame_time)
            
            # Find analysis index closest to frame_time
            analysis_idx = np.searchsorted(time_axis, frame_time)
            analysis_idx = min(analysis_idx, len(time_axis) - 1)
            
            # Get local reactivity parameters
            bass_val = bass_envelope[analysis_idx] if len(bass_envelope) > 0 else 0
            rms_val = rms_envelope[analysis_idx] if len(rms_envelope) > 0 else 0
            fft_row = fft_data[analysis_idx] if len(fft_data) > 0 else None
            
            # B. Apply Zoom effect (bass driven)
            if bass_zoom_sens > 0 and bass_val > 0.1:
                zoom_factor = 1.0 + (bass_val * 0.08 * bass_zoom_sens)
                new_w = int(target_w * zoom_factor)
                new_h = int(target_h * zoom_factor)
                zoomed = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                
                # Crop back to center
                sx = (new_w - target_w) // 2
                sy = (new_h - target_h) // 2
                frame = zoomed[sy:sy+target_h, sx:sx+target_w]
            
            # C. Apply Color Filter
            if color_filter != 'none':
                frame = apply_color_filter(frame, color_filter)
                
            # D. Apply Flash effect (bass driven)
            if bass_flash_sens > 0 and bass_val > 0.7:
                flash_intensity = (bass_val - 0.7) / 0.3 * bass_flash_sens
                frame = cv2.addWeighted(frame, 1.0 - (flash_intensity * 0.5), white_overlay, flash_intensity * 0.5, 0)
                
            # E. Apply Glitch effect
            if glitch_sens > 0 and bass_val > 0.85:
                # Random probability to glitch on heavy beats
                if np.random.rand() < 0.4:
                    glitch_calc_intensity = (bass_val - 0.8) / 0.2 * glitch_sens * glitch_intensity_factor
                    frame = apply_glitch(frame, glitch_calc_intensity)
            
            # F. Draw Audio Visualizer
            if visualizer_type != 'none':
                draw_visualizer(frame, fft_row, visualizer_type, visualizer_color, target_w, target_h)
                
            # G. Find active lyrics
            active_lyric = None
            for lyr in lyrics:
                if lyr["start"] <= frame_time <= lyr["end"]:
                    active_lyric = lyr
                    break
            
            # H. Draw Lyrics
            if active_lyric:
                frame = draw_lyrics_pil(
                    frame=frame,
                    active_lyric=active_lyric,
                    frame_time=frame_time,
                    font_family=font_family,
                    font_size=font_size,
                    font_color_hex=font_color,
                    outline_color_hex=outline_color,
                    outline_width=outline_width,
                    position=text_position,
                    y_offset=text_y_offset,
                    target_w=target_w,
                    target_h=target_h,
                    karaoke_effect=karaoke_effect,
                    custom_font_path=custom_font_path
                )
                
            # I. Write frame to FFmpeg pipe
            process.stdin.write(frame.tobytes())
            
            # Update progress
            if progress_callback and f_idx % max(1, total_frames // 100) == 0:
                pct = int((f_idx / total_frames) * 100)
                progress_callback(pct)
                
    except Exception as e:
        print(f"[ERROR] Video generation frame loop failed: {e}", flush=True)
        raise e
    finally:
        media_mgr.close()
        # Close stdin so ffmpeg knows we're done sending frames
        if process.stdin:
            try:
                process.stdin.close()
            except Exception:
                pass
        # Wait for ffmpeg to finish encoding
        process.wait()
        # Wait for stderr drain thread
        stderr_thread.join(timeout=5)
        if process.returncode != 0:
            err_detail = "\n".join(stderr_lines[-20:]) if stderr_lines else "(no stderr captured)"
            print(f"[ERROR] FFmpeg failed (code {process.returncode}):\n{err_detail}", flush=True)
            raise RuntimeError(f"FFmpeg failed (code {process.returncode}): {err_detail}")

    if progress_callback:
        progress_callback(100)
