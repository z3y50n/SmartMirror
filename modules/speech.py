import json
import os

import speech_recognition as sr

CONFIG_PATH = os.path.join(os.path.dirname(
    os.path.abspath("config.json")), "config.json")


class Speech():
    def __init__(self, launch_phrase):
        self._launch_phrase = launch_phrase
        self._r = sr.Recognizer()
        self._audio = None
        self._text = ""

    def get_text(self):
        return self._text

    def listen_for_audio(self):
        m = sr.Microphone()
        with m as source:
            self._r.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")
            self._audio = self._r.listen(source, phrase_time_limit=2.5)

    def speech_to_text(self):
        try:
            self._text = self._r.recognize_google(self._audio)
        except sr.UnknownValueError:
            self._text = ""
            print("I could not understand you")

    def check_launch_phrase(self):
        if self._text == self._launch_phrase:
            return True
        return False


if __name__ == "__main__":
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    s = Speech(cfg["launch_phrase"])

    while not s.check_launch_phrase():
        s.listen_for_audio()
        s.speech_to_text()
        print(s.get_text())
