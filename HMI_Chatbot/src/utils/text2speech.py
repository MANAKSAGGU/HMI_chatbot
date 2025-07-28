import pyttsx3
import tempfile
import os

class TTSTalker:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)

    def test(self, text):
        if not text.strip():
            return None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            filename = fp.name

        self.engine.save_to_file(text, filename)
        self.engine.runAndWait()
        return filename
