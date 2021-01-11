import os

from configparser import ConfigParser
import os
import threading

from modules import speech

CONFIG_PATH = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "smartmirror.ini")


class MainController(threading.Thread):
    def __init__(self, gui):
        super(MainController, self).__init__()
        config = ConfigParser()
        config.read(CONFIG_PATH)

        self._s = speech.Speech(
            config["Speech"]["launch_phrase"], config["Speech"]["close_phrase"])
        self._gui = gui

        self.daemon = True
        self.start()

    def run(self):
        self._authenticate()
        self.decide_action()

    def _authenticate(self):
        while not self._s.check_launch_phrase():
            self._s.speak()
        print("You gained access")

    def _decide_action(self):
        while not self._s.check_close_phrase():
            self._s.speak()


if __name__ == "__main__":
    interface = MainController()
