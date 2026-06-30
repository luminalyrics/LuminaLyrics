import os
import subprocess
import tempfile
import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, lfilter, find_peaks

def convert_to_wav(input_path: str) -> str:
    """
    Converts any audio file to a standard mono 22050Hz WAV file using FFmpeg.
    Returns the path to the temporary WAV file.
    """
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, "visualizer_temp.wav")
    
    # Force conversion to 22050Hz, mono, 16-bit PCM WAV
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "22050",
        "-c:a", "pcm_s16le",
        output_path
    ]
    
    try:
        # Run FFmpeg and suppress output
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        # If FFmpeg failed, write standard print and raise
        print(f"FFmpeg conversion failed: {e.stderr.decode('utf-8', errors='ignore')}")
        raise RuntimeError("FFmpeg non trouvé ou incapable de convertir le fichier audio. Assurez-vous que FFmpeg est installé.")

def analyze_audio(audio_path: str):
    """
    Analyzes the audio file:
    1. Converts it to a mono 22050Hz WAV.
    2. Detects BPM and beat timestamps.
    3. Calculates RMS (volume) and bass energy over time.
    4. Computes FFT/spectrum data for the visualizer.
    
    Returns a dict with:
      - duration (float)
      - bpm (float)
      - beats (list of floats)
      - rms_envelope (numpy array)
      - bass_envelope (numpy array)
      - fft_data (numpy array of spectrum values over time)
      - time_axis (numpy array of timestamps corresponding to FFT/envelope frames)
    """
    # 1. Convert to WAV
    wav_path = convert_to_wav(audio_path)
    
    try:
        # 2. Read WAV file
        sr, y = wavfile.read(wav_path)
        
        # Convert to float32 normalized between -1.0 and 1.0
        y = y.astype(np.float32) / 32768.0
        
        duration = len(y) / sr
        
        # 3. Calculate Envelopes (Volume and Bass)
        # We will use frame sizes of 1024 samples (approx. 46ms at 22050Hz) with 512 samples overlap
        hop_length = 512
        frame_length = 1024
        
        # Number of frames
        num_frames = (len(y) - frame_length) // hop_length + 1
        time_axis = np.arange(num_frames) * hop_length / sr
        
        rms_envelope = np.zeros(num_frames)
        bass_envelope = np.zeros(num_frames)
        
        # Design a butterworth lowpass filter for bass (cutoff around 130Hz)
        nyq = 0.5 * sr
        low = 130.0 / nyq
        b, a = butter(4, low, btype='low')
        y_bass = lfilter(b, a, y)
        
        # Pre-calculate FFT spectrum data
        # We want to divide the spectrum into N bins (e.g. 32 bins) for the visualizer
        num_spec_bins = 32
        fft_data = np.zeros((num_frames, num_spec_bins))
        
        # Apply Hanning window
        window = np.hanning(frame_length)
        
        for i in range(num_frames):
            start_sample = i * hop_length
            end_sample = start_sample + frame_length
            
            frame = y[start_sample:end_sample]
            frame_bass = y_bass[start_sample:end_sample]
            
            # RMS (General volume)
            rms_envelope[i] = np.sqrt(np.mean(frame**2)) if len(frame) > 0 else 0
            # Bass energy
            bass_envelope[i] = np.sqrt(np.mean(frame_bass**2)) if len(frame_bass) > 0 else 0
            
            # FFT for visualizer
            if len(frame) == frame_length:
                windowed_frame = frame * window
                fft_vals = np.abs(np.fft.rfft(windowed_frame))
                # Group FFT bins logarithmically into 32 bands
                # At 22050Hz, rfft has 513 bins (from 0 to 11025 Hz)
                # We group them to make the visualizer react nicely to low/mid/high frequencies
                if len(fft_vals) >= 513:
                    # Logarithmic spacing
                    indices = np.logspace(0, np.log10(256), num_spec_bins + 1, dtype=int)
                    for b_idx in range(num_spec_bins):
                        start_bin = indices[b_idx]
                        end_bin = max(indices[b_idx + 1], start_bin + 1)
                        # Take average energy in this frequency band
                        fft_data[i, b_idx] = np.mean(fft_vals[start_bin:end_bin])
        
        # Normalize FFT data slightly for display comfort
        if np.max(fft_data) > 0:
            fft_data = fft_data / np.max(fft_data)
            
        # Normalize envelopes
        if np.max(rms_envelope) > 0:
            rms_envelope = rms_envelope / np.max(rms_envelope)
        if np.max(bass_envelope) > 0:
            bass_envelope = bass_envelope / np.max(bass_envelope)
            
        # 4. Beat Detection
        # We look at the positive difference (onset strength) of the bass envelope
        bass_diff = np.diff(bass_envelope)
        bass_onset = np.clip(bass_diff, 0, None)
        # Pad with 0 to match length
        bass_onset = np.append(bass_onset, 0)
        
        # Find peaks in the bass onset envelope
        # To avoid multiple peaks too close, we set min distance (e.g. 0.3s)
        min_dist_frames = int(0.3 * sr / hop_length) # approx 0.3 seconds
        peaks, _ = find_peaks(bass_onset, distance=min_dist_frames, prominence=0.1)
        
        beat_timestamps = time_axis[peaks].tolist()
        
        # Estimate BPM
        if len(beat_timestamps) > 1:
            intervals = np.diff(beat_timestamps)
            median_interval = np.median(intervals)
            bpm = 60.0 / median_interval if median_interval > 0 else 120.0
        else:
            bpm = 120.0
            # Fallback: create periodic beats if none detected
            beat_timestamps = np.arange(0, duration, 0.5).tolist() # 120 BPM = 0.5s interval
            
        # Clean up temp wav file
        try:
            os.remove(wav_path)
        except Exception:
            pass
            
        return {
            "duration": duration,
            "bpm": bpm,
            "beats": beat_timestamps,
            "rms_envelope": rms_envelope,
            "bass_envelope": bass_envelope,
            "fft_data": fft_data,
            "time_axis": time_axis
        }
        
    except Exception as e:
        # Clean up temp wav file in case of error
        try:
            os.remove(wav_path)
        except Exception:
            pass
        raise e
