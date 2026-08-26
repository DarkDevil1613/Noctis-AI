import sys
import codecs
sys.stdout.reconfigure(encoding='utf-8')
import re
import time
import os
import threading
import numpy as np
import sounddevice as sd
import wave
import tempfile
import onnxruntime as ort
import winsound
from colorama import init, Fore, Style
init(autoreset=True)

# Load Silero VAD globally
_vad_path = os.path.join(os.path.dirname(__file__), 'voice', 'silero_vad.onnx')
_vad_session = ort.InferenceSession(_vad_path)

from core.noctis_core import NoctisCore
from voice.stt import SpeechToText
from voice.vocabulary_hints import PROJECT_VOCABULARY
from tools.system_control import SystemControl
from config import NOCTIS_NAME, OWNER_NAME, WAKE_WORDS, STANDBY_WORDS, STATE_STANDBY, STATE_ACTIVE
import pyttsx3
from dotenv import load_dotenv
load_dotenv()

# WebSocket bridge for UI events
try:
    from api.ws_bridge import broadcast as ws_broadcast
except Exception:
    def ws_broadcast(event, data): pass

# ──────────────────────────────────────────────
#  SYSTEM PROMPT
# ──────────────────────────────────────────────
from config import VOICE_SYSTEM_PROMPT

# ──────────────────────────────────────────────
#  SYSTEM CONTROL
# ──────────────────────────────────────────────
sc = SystemControl()

SYSTEM_COMMANDS = [
    (["cpu", "processor usage", "processor load"],          lambda _: sc.get_cpu()),
    (["ram", "memory usage", "memory"],                     lambda _: sc.get_ram()),
    (["battery", "power level", "charge"],                  lambda _: sc.get_battery()),
    (["disk", "storage", "drive space"],                    lambda _: sc.get_disk()),
    (["network", "internet speed", "bandwidth"],            lambda _: sc.get_network()),
    (["uptime", "how long running", "running time"],        lambda _: sc.get_uptime()),
    (["system stats", "system status", "full stats"],       lambda _: sc.get_system_stats()),
    (["full report", "diagnostics", "system report"],       lambda _: sc.full_report()),
    (["wifi", "wi-fi", "wireless", "signal"],               lambda _: sc.get_wifi_info()),
    (["ip address", "my ip", "network address"],            lambda _: sc.get_ip()),
    (["volume up"],                                         lambda _: sc.volume_up()),
    (["volume down"],                                       lambda _: sc.volume_down()),
    (["what's my volume", "current volume", "volume level", "get volume", "what is my volume", "whats my volume"], lambda _: sc.get_volume()),
    (["mute", "silence audio"],                             lambda _: sc.mute()),
    (["unmute", "restore audio"],                           lambda _: sc.unmute()),
    (["lock", "lock screen", "lock the screen"],            lambda _: sc.lock()),
    (["sleep mode", "go to sleep", "suspend"],              lambda _: sc.sleep()),
    (["screenshot", "take a screenshot", "capture screen"], lambda _: sc.take_screenshot()),
    (["active window", "what's open", "current window"],   lambda _: sc.get_active_window()),
    (["clipboard", "what's in clipboard"],                  lambda _: sc.get_clipboard()),
    (["processes", "top processes", "running apps"],        lambda _: sc.list_processes()),
    (["temperature", "cpu temp", "how hot"],                lambda _: sc.get_temperature()),
    (["brightness"],                                        lambda _: sc.get_brightness()),
]

def match_system_command(text):
    t = text.lower().strip()

    # Set volume
    m = re.search(r'(?:set volume|volume|make.*volume|set.*volume)\s+(?:to\s+)?(\d+)', t)
    if m:
        return sc.set_volume(int(m.group(1)))

    # Set brightness
    m = re.search(r'(?:set brightness|brightness)\s+(?:to\s+)?(\d+)', t)
    if m:
        return sc.set_brightness(int(m.group(1)))

    # Open folder
    m = re.search(r'(?:open|show)\s+(?:my\s+)?(.+?)\s+folder', t)
    if m:
        return sc.open_folder(m.group(1).strip())

    m = re.search(r'open folder\s+(.+)', t)
    if m:
        return sc.open_folder(m.group(1).strip())

    # Search web
    m = re.search(r'(?:search for|search web for|google)\s+(.+)', t)
    if m:
        return sc.search_web(m.group(1).strip())

    # Go to URL / website
    m = re.search(r'(?:go to|open website)\s+(.+)', t)
    if m:
        return sc.open_url(m.group(1).strip())

    # Open / launch app or URL
    m = re.search(r'(?:open|launch|start)\s+(.+)', t)
    if m:
        target = m.group(1).strip()
        # Remove trailing words like "app" or "please"
        target = re.sub(r'\s+(app|program|please)$', '', target)
        return sc.launch_app(target)

    # Close / kill process
    m = re.search(r'(?:close|kill|terminate)\s+(.+)', t)
    if m:
        return sc.kill_process(m.group(1).strip())

    if any(w in t for w in ["shutdown", "shut down", "power off", "turn off the computer"]):
        return sc.shutdown(confirmed=True)

    if any(w in t for w in ["restart", "reboot"]):
        return sc.restart(confirmed=True)

    if any(w in t for w in ["cancel shutdown", "abort shutdown"]):
        return sc.cancel_shutdown()

    for keywords, handler in SYSTEM_COMMANDS:
        if any(kw in t for kw in keywords):
            return handler(t)

    return None

# ──────────────────────────────────────────────
#  TTS — Edge TTS (natural neural voice)
# ──────────────────────────────────────────────
def speak(text):
    try:
        from voice.tts_edge import speak as edge_speak
        edge_speak(text)
    except Exception as e:
        print(f"[TTS Fallback] Edge TTS failed: {e}, using pyttsx3")
        import re
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'#+', '', text)
        text = re.sub(r'`+', '', text)
        text = re.sub(r'\d+\.', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        engine = pyttsx3.init()
        engine.setProperty('rate', 145)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()

# ──────────────────────────────────────────────
#  AUDIO RECORDER
# ──────────────────────────────────────────────
def record_with_silence(
    sample_rate=16000,
    silence_threshold=0.3,
    silence_duration=0.5,    # Reduced from 1.2s — cuts off faster after speech ends
    max_duration=30.0,
):
    chunk_size = 512
    silence_limit = int((silence_duration * sample_rate) / chunk_size)
    max_chunks    = int((max_duration * sample_rate) / chunk_size)
    pre_roll_chunks = int((0.15 * sample_rate) / chunk_size)  # 150ms pre-buffer

    import collections
    pre_buffer     = collections.deque(maxlen=pre_roll_chunks)
    frames         = []
    silent_count   = 0
    speech_started = False
    
    state = np.zeros((2, 1, 128), dtype=np.float32)
    sr = np.array(16000, dtype=np.int64)

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        # Mic is now initialized. Play a high beep to signal 'Listening'
        winsound.Beep(1000, 150)
        
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            chunk_flat = chunk.flatten()
            
            audio_float32 = chunk_flat.astype(np.float32) / 32768.0
            inputs = {'input': audio_float32[np.newaxis, :], 'state': state, 'sr': sr}
            out, state = _vad_session.run(None, inputs)
            prob = out[0][0]

            if not speech_started:
                pre_buffer.append(chunk_flat.copy())
                if prob > silence_threshold:
                    speech_started = True
                    # Include pre-roll buffer so we don't lose the first syllable
                    frames.extend(list(pre_buffer))
                    silent_count = 0
            else:
                frames.append(chunk_flat.copy())
                if prob > silence_threshold:
                    silent_count = 0
                else:
                    silent_count += 1
                    if silent_count >= silence_limit:
                        break
        
        # Play a low beep to signal 'Processing'
        winsound.Beep(600, 150)

    if not frames:
        return np.zeros((512, 1), dtype=np.int16)
    return np.concatenate(frames, axis=0)[:, np.newaxis]


def audio_to_wav_file(audio, sample_rate=16000):
    tmp  = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    path = tmp.name
    tmp.close()
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return path


def audio_to_wav_bytes(audio, sample_rate=16000):
    """Convert audio numpy array to in-memory WAV bytes (no disk I/O)."""
    import io
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    wav_buffer.seek(0)
    wav_buffer.name = "audio.wav"
    return wav_buffer


def transcribe_audio(groq_client, audio, sample_rate=16000):
    """Transcribe audio using Groq Whisper turbo — zero disk I/O, max speed."""
    wav_buffer = audio_to_wav_bytes(audio, sample_rate)
    try:
        result = groq_client.audio.transcriptions.create(
            file=wav_buffer,
            model="whisper-large-v3-turbo",
            language="en",
            temperature=0.0,
            prompt=PROJECT_VOCABULARY
        )
        return result.text.strip()
    except Exception as e:
        print(f"[Groq STT Error] {e}")
        return ""

# ──────────────────────────────────────────────
#  WAKE WORD DETECTION
# ──────────────────────────────────────────────
def contains_wake_word(text):
    t = text.lower()
    return any(w in t for w in WAKE_WORDS)

def contains_standby_word(text):
    t = text.lower()
    return any(w in t for w in STANDBY_WORDS)

# ──────────────────────────────────────────────
#  WAKE WORD DETECTION — UPGRADED
# ──────────────────────────────────────────────
def listen_for_wake_word(groq_client):
    """
    Runs in a tight loop with minimal audio chunks.
    Only sends audio to Groq if volume is high enough — saves API calls.
    Uses a short 2s window for speed. Resets immediately after detection.
    """
    sample_rate     = 16000
    chunk_duration  = 2.0          # seconds per listen window — short = fast
    chunk_size      = int(sample_rate * chunk_duration)
    vol_threshold   = 80           # ignore silence completely — lower = more sensitive
    
    print(f"{Fore.MAGENTA}[WAKE] Passive listening active...{Style.RESET_ALL}")
    
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        while True:
            chunk, _ = stream.read(chunk_size)
            chunk    = chunk.flatten()
            vol      = np.abs(chunk).mean()
            
            # Skip silent audio — no API call wasted
            if vol < vol_threshold:
                continue
            
            # Only transcribe if there's actual sound
            wav_buffer = audio_to_wav_bytes(chunk.reshape(-1, 1), sample_rate)
            try:
                result = groq_client.audio.transcriptions.create(
                    file=wav_buffer,
                    model="whisper-large-v3-turbo",
                    language="en",
                    temperature=0.0,
                    prompt=PROJECT_VOCABULARY
                )
                text = result.text.strip().lower()
                if text:
                    print(f"{Fore.MAGENTA}[WAKE] heard: '{text}'{Style.RESET_ALL}")
                if contains_wake_word(text):
                    return text
            except Exception as e:
                print(f"{Fore.RED}[WAKE ERROR] {e}{Style.RESET_ALL}")


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    print(f"{Fore.CYAN}[DEVILCORE] Initializing voice systems...{Style.RESET_ALL}")

    from groq import Groq
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    noctis = NoctisCore()
    stt    = SpeechToText()

    noctis.system_prompt        = VOICE_SYSTEM_PROMPT
    noctis.conversation_history = []

    state = STATE_STANDBY

    speak("NOCTIS online. Awaiting your command, Master.")
    print(f"\n{Fore.GREEN}[{NOCTIS_NAME}] Hands-free mode active.")
    print(f"  Wake words : {', '.join(w.upper() for w in WAKE_WORDS)}")
    print(f"  Standby    : {', '.join(w.upper() for w in STANDBY_WORDS)}")
    print(f"  Quit       : say 'exit noctis' or Ctrl+C{Style.RESET_ALL}\n")
    print(f"{Fore.MAGENTA}[STATUS] STANDBY — say SHADOW or ACTIVATE to wake...{Style.RESET_ALL}")

    while True:
        try:
            # ── STANDBY ──────────────────────────────────
            if state == STATE_STANDBY:
                listen_for_wake_word(groq_client)
                state = STATE_ACTIVE
                print(f"\n{Fore.GREEN}[STATUS] ACTIVE — speak your command.{Style.RESET_ALL}")
                ws_broadcast("status", "active")
                speak("Yes, Master.")

            # ── ACTIVE ───────────────────────────────────
            # DESIGN DECISION: Active session is CONTINUOUS-GATED, not push-to-talk.
            # - record_with_silence captures audio until a 2.5s silence gap is detected.
            # - To prevent spamming Groq Whisper API on pure ambient noise or long silences,
            #   we enforce a double threshold:
            #     1) A local peak gate (VAD prob > 0.5) to start the silence countdown.
            #     2) A global mean gate (np.abs(audio).mean() < 5) to discard purely ambient clips.
            if state == STATE_ACTIVE:
                print(f"{Fore.YELLOW}[Listening...]{Style.RESET_ALL}")
                ws_broadcast("voice_state", "listening")
                audio = record_with_silence()  # Now uses defaults inside the function           
                ws_broadcast("voice_state", "processing")
                vol = np.abs(audio).mean()
                if vol < 5:
                    print(f"{Fore.RED}[STT] Nothing heard (VAD passed but volume extremely low). Say something!...{Style.RESET_ALL}")
                    continue

                text = transcribe_audio(groq_client, audio)
                if not text:
                    print(f"{Fore.RED}[STT] Nothing heard (Silence leaked to Whisper). Say something!...{Style.RESET_ALL}")
                    continue

                print(f"{Fore.YELLOW}Master (voice){Style.RESET_ALL} » {text}")
                ws_broadcast("transcription", text)
                t_lower = text.lower().strip()

                # ── Standby trigger ──
                if contains_standby_word(t_lower):
                    state = STATE_STANDBY
                    ws_broadcast("status", "standby")
                    ws_broadcast("voice_state", "idle")
                    speak("Going dark.")
                    print(f"{Fore.MAGENTA}[STATUS] STANDBY — say SHADOW or ACTIVATE to wake...{Style.RESET_ALL}")
                    continue

                # ── Exit trigger ──
                exit_phrases = ["exit", "shutdown", "goodbye", "shut down", "close", "bye", "turn off", "stop", "exit now", "good bye"]
                if any(w in t_lower for w in exit_phrases):
                    speak("Session complete. Returning to the shadows.")
                    break

                # ── System control ──
                sys_result = match_system_command(text)
                if sys_result:
                    speech_text = sys_result
                    if len(sys_result) > 300:
                        lines       = sys_result.strip().splitlines()
                        speech_text = " ".join(lines[:4])
                    print(f"{Fore.CYAN}{NOCTIS_NAME}{Style.RESET_ALL}: {sys_result}")
                    ws_broadcast("llm_done", sys_result)
                    speak(speech_text)
                else:
                    # ── LLM ──
                    response = noctis.chat(text, stream=False)
                    print(f"{Fore.CYAN}{NOCTIS_NAME}{Style.RESET_ALL}: {response}")
                    ws_broadcast("llm_done", response)
                    speak(response)

                ws_broadcast("voice_state", "idle")
                time.sleep(0.3)

        except KeyboardInterrupt:
            print(f"\n{Fore.CYAN}[DEVILCORE] Corrupted.{Style.RESET_ALL}")
            break
        except Exception as e:
            err_msg = f"A critical error occurred: {str(e)}"
            print(f"{Fore.RED}[CRASH PREVENTED] {err_msg}{Style.RESET_ALL}")
            speak("I encountered an internal error, but I am still online.")
            time.sleep(1)

if __name__ == "__main__":
    main()