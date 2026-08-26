import openwakeword
from openwakeword.model import Model
import sounddevice as sd
import numpy as np
import threading

class WakeWordDetector:
    def __init__(self, on_detected_callback):
        self.callback = on_detected_callback
        self.running = False
        self.thread = None
        self.sample_rate = 16000
        self.chunk_size = 1280
        self.threshold = 0.5  # raise to 0.7 if too many false triggers

        # Download built-in models automatically
        openwakeword.utils.download_models()
        self.model = Model(
            wakeword_models=["hey_jarvis"],  # closest to Noctis vibe, free built-in
            inference_framework="onnx"
        )

    def _detect_loop(self):
        print("[WakeWord] Always listening... say 'Hey Jarvis' to activate Noctis")
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=self.chunk_size
        ) as stream:
            while self.running:
                chunk, _ = stream.read(self.chunk_size)
                chunk = chunk.flatten()
                prediction = self.model.predict(chunk)
                for name, score in prediction.items():
                    if score > self.threshold:
                        print(f"[WakeWord] Triggered — score: {score:.2f}")
                        self.model.reset()
                        self.callback()
                        break

    def start(self):
        self.running = True
        self.thread = threading.Thread(
            target=self._detect_loop,
            daemon=True
        )
        self.thread.start()

    def stop(self):
        self.running = False