from typing import List, Dict
from faster_whisper import WhisperModel
import os

# Load environment variables
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

_whisper = WhisperModel(
    WHISPER_MODEL_SIZE,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE
)

def transcribe(audio_path: str) -> List[Dict]:
    """
    Transcribe an audio file using faster-whisper and return our standard
    list of segments: [{start, end, speaker, text}].
    """
    # beam_size=1 is fastest; raise for a bit more accuracy.
    segments, info = _whisper.transcribe(
        audio_path,
        language="en",         
        vad_filter=True,      
        beam_size=1
    )

    out = []
    for seg in segments:
        out.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "speaker": "A",    # no diarization here; we can add later
            "text": seg.text.strip()
        })

    # If there were no segments (edge case), return a single empty segment
    if not out:
        out = [{"start": 0.0, "end": 0.0, "speaker": "A", "text": ""}]

    return out
