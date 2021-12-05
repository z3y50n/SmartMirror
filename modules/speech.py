from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import os

import speech_recognition as sr


class Speech:
    def __init__(self):
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

    def listen(self, label=None):
        self._listen_for_audio(label)
        self._speech_to_text()
        print(self._text)
        return self._text

    def speak_back(self, text):
        tts = gTTS(text=text, lang="en")
        tts.save("temp.mp3")
        speech = AudioSegment.from_mp3("temp.mp3")
        play(speech)
        os.remove("temp.mp3")
