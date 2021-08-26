from configparser import ConfigParser
import os
import threading

from modules import action, bot, speech, face_recognition
from modules.basedir import BASEDIR

CONFIG_PATH = os.path.join(BASEDIR, "smartmirror.ini")
FACE_MODEL = os.path.join(BASEDIR, "assets", "facial_recognition_model.xml")

class Controller(threading.Thread):
    def __init__(self, gui):
        super(Controller, self).__init__()
        config = ConfigParser()
        config.read(CONFIG_PATH)

        self._launch_phrase = config["Speech"]["launch_phrase"]
        self._close_phrase = config["Speech"]["close_phrase"]
        self._s = speech.Speech()
        self._gui = gui
        self._widgets = {id: widget for id, widget in self._gui.root.ids.items()}

        self._bot = bot.Bot()
        self._action = action.Action(self._gui)

        self._running = threading.Event()
        self.daemon = True
        self.start()

    def _check_launch_phrase(self, text):
        if text == self._launch_phrase:
            return True
        return False

    def _check_close_phrase(self, text):
        if text == self._close_phrase:
            return True
        return False

    def _check_close(self, text):
        if text == "quit" or text == "exit":
            self._s.speak_back("Goodbye!")
            self._gui.stop()

    def pause(self):
        self._running.clear()

    def resume(self):
        self._running.set()

    def run(self):
        self.resume()
        self._authenticate_mode()
        self._command_mode()

    def _authenticate_mode(self):
        text = self._s.listen(self._gui.root.ids['status_label'])
        while not self._check_launch_phrase(text):
            self._check_close(text)
            text = self._s.listen(self._gui.root.ids['status_label'])

        print("You gained access")
        self._s.speak_back("How may I help you?")

    def _command_mode(self):
        text = self._s.listen(self._gui.root.ids['status_label'])
        while not self._check_close_phrase(text):
            self._running.wait()
            
            self._check_close(text)
            
            resp = self._bot.message(text)
            if resp:
                print(resp)
                self._action.perform(resp)
                
            text = self._s.listen(self._gui.root.ids['status_label'])
        self.run()
