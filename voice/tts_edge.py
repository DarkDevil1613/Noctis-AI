"""
DevilCore — Noctis Edge TTS Module
voice/tts_edge.py
Uses Microsoft Edge TTS (free, neural voices) for natural speech synthesis.
"""

import asyncio
import io
import os
import tempfile
import subprocess
import threading

# Default voice — deep male, fits Noctis character
DEFAULT_VOICE = "en-US-GuyNeural"
DEFAULT_RATE = "+5%"  # Slightly faster for snappy responses


def _run_edge_tts_sync(text: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> str:
    """Generate speech audio file using edge-tts CLI. Returns path to MP3 file."""
    import edge_tts

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = tmp.name
    tmp.close()

    async def _generate():
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(tmp_path)

    # Run async edge-tts in a new event loop (safe from any thread)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_generate())
    finally:
        loop.close()

    return tmp_path


def speak(text: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE):
    """
    Speak text using Edge TTS with playback via Windows built-in player.
    Blocks until speech is complete.
    """
    import re
    # Clean markdown artifacts from LLM responses
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'`+', '', text)
    text = re.sub(r'\d+\.', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return

    try:
        mp3_path = _run_edge_tts_sync(text, voice, rate)

        # Play using PowerShell's built-in media player (no extra deps needed)
        # Uses Windows Media Player COM object for MP3 playback
        ps_cmd = (
            f'$p = New-Object System.Media.SoundPlayer; '
            f'Add-Type -AssemblyName presentationCore; '
            f'$m = New-Object System.Windows.Media.MediaPlayer; '
            f'$m.Open([Uri]::new("{mp3_path}")); '
            f'Start-Sleep -Milliseconds 200; '
            f'$m.Play(); '
            f'Start-Sleep -Milliseconds ($m.NaturalDuration.TimeSpan.TotalMilliseconds + 500); '
            f'$m.Close()'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print(f"[Edge TTS Error] {e}")
        # Fallback to pyttsx3 if edge-tts fails
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 145)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            pass
    finally:
        try:
            os.unlink(mp3_path)
        except Exception:
            pass


def speak_async(text: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE):
    """Non-blocking speak — runs TTS in a background thread."""
    t = threading.Thread(target=speak, args=(text, voice, rate), daemon=True)
    t.start()
    return t
