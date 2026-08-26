import sounddevice as sd
import numpy as np
import wave
import tempfile
import os
from groq import Groq
from dotenv import load_dotenv
from voice.vocabulary_hints import PROJECT_VOCABULARY

load_dotenv()

class SpeechToText:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.sample_rate = 16000
        self.channels = 1
        self.silence_threshold = 600
        self.silence_duration = 3.0
        self.max_duration = 30

    def transcribe(self, duration=None):
        print("[Noctis] Listening... (speak now, will stop after 3s silence)")
        chunk_size = int(self.sample_rate * 0.1)
        silence_chunks = int(self.silence_duration / 0.1)
        max_chunks = int(self.max_duration / 0.1)

        frames = []
        silent_count = 0
        speaking_started = False

        with sd.InputStream(samplerate=self.sample_rate,
                           channels=self.channels,
                           dtype='int16') as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(chunk_size)
                frames.append(chunk.copy())
                volume = np.abs(chunk).mean()

                if volume > self.silence_threshold:
                    speaking_started = True
                    silent_count = 0
                elif speaking_started:
                    silent_count += 1
                    if silent_count >= silence_chunks:
                        print("[Noctis] Speech ended.")
                        break

        if not frames:
            return ""

        audio = np.concatenate(frames, axis=0)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())

        try:
            with open(tmp_path, "rb") as f:
                result = self.client.audio.transcriptions.create(
                    file=("audio.wav", f),
                    model="whisper-large-v3",
                    language="en",
                    prompt=PROJECT_VOCABULARY
                )
            return result.text.strip()
        except Exception as e:
            print(f"[Noctis STT Error] {e}")
            return ""
        finally:
            os.unlink(tmp_path)