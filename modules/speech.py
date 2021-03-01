from configparser import ConfigParser
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import os
from kivy import config

import speech_recognition as sr

CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(
    __file__, os.path.pardir, os.path.pardir)), "smartmirror.ini")


class Speech():
    def __init__(self, launch_phrase, close_phrase):
        self._launch_phrase = launch_phrase
        self._close_phrase = close_phrase
        self._r = sr.Recognizer()
        self._audio = None
        self._text = ""

    def get_text(self):
        return self._text

    def _listen_for_audio(self, label=None):
        m = sr.Microphone()
        with m as source:
            self._r.adjust_for_ambient_noise(source, duration=1)
            if label:
                label.text = "Listening..."
            print("Listening...")
            self._audio = self._r.listen(source, phrase_time_limit=5)
            if label:
                label.text = ""

    def _speech_to_text(self):
        try:
            self._text = self._r.recognize_google(self._audio)
        except sr.UnknownValueError:
            self._text = ""
            print("I could not understand you")

    def check_launch_phrase(self):
        if self._text == self._launch_phrase:
            return True
        return False

    def check_close_phrase(self):
        if self._text == self._close_phrase:
            return True
        return False

    def speak(self, label=None):
        self._listen_for_audio(label)
        self._speech_to_text()
        print(self._text)

    def speak_back(text):
        tts = gTTS(text=text, lang='en')
        tts.save("temp.mp3")
        speech = AudioSegment.from_mp3('temp.mp3')
        play(speech)
        os.remove("temp.mp3")


if __name__ == "__main__":
    config = ConfigParser()
    config.read(CONFIG_PATH)
    cfg = config["Speech"]

    s = Speech(cfg["launch_phrase"], cfg["close_phrase"])

    while not s.check_launch_phrase():
        s.speak()
