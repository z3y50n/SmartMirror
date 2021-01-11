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
        
        self._running = threading.Event()
        self.daemon = True
        self.start()

    def pause(self):
        self._running.clear()
    
    def resume(self):
        self._running.set()

    def run(self):
        self.resume()
        self._authenticate()
        self._decide_action()

    def _authenticate(self):
        while not self._s.check_launch_phrase():
            self._s.speak(self._gui.root.ids['status_label'])
        print("You gained access")

    def _decide_action(self):
        while not self._s.check_close_phrase():
            self._running.wait()
            self._s.speak()


if __name__ == "__main__":
    interface = MainController()
