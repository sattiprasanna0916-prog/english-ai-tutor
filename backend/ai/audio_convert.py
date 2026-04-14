import os
import subprocess
import tempfile

def ensure_wav_16k_mono(input_path: str) -> str:
    """
    Converts any audio file to WAV 16kHz mono.
    Returns the wav path (new file). Caller should delete it.
    """
    out_fd, out_path = tempfile.mkstemp(suffix=".wav")
    os.close(out_fd)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        "-vn",
        out_path
    ]

    # Hide ffmpeg spam; if ffmpeg missing this will throw
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_path