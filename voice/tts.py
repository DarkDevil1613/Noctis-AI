import pyttsx3
import threading
import re

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 145)
        self.engine.setProperty('volume', 1.0)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id)

    def clean_text(self, text):
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'#+', '', text)
        text = re.sub(r'+', '', text)
        text = re.sub(r'\d+\.', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def speak(self, text):
        text = self.clean_text(text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunk = ""
        for sentence in sentences:
            if len(chunk) + len(sentence) < 200:
                chunk += " " + sentence
            else:
                if chunk.strip():
                    self.engine.say(chunk.strip())
                    self.engine.runAndWait()
                chunk = sentence
        if chunk.strip():
            self.engine.say(chunk.strip())
            self.engine.runAndWait()

    def speak_async(self, text):
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()


# Module-level speak function for direct import
_tts_instance = None

def speak(text: str):
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    _tts_instance.speak(text)
