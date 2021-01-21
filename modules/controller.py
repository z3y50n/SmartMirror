from configparser import ConfigParser
import os
import threading

from modules import action, bot, speech 

CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir)), "smartmirror.ini")


class Controller(threading.Thread):
    def __init__(self, gui):
        super(Controller, self).__init__()
        config = ConfigParser()
        config.read(CONFIG_PATH)

        self._s = speech.Speech(config["Speech"]["launch_phrase"], 
                                config["Speech"]["close_phrase"])
        self._gui = gui
        self._widgets = {id: widget for id, widget in self._gui.root.ids.items()}

        self._bot = bot.Bot()
        self._action = action.Action(self._gui)

        self._running = threading.Event()
        self.daemon = True
        self.start()

    def pause(self):
        self._running.clear()

    def resume(self):
        self._running.set()

    def run(self):
        self.resume()
        self._authenticate_mode()
        self._command_mode()

    def _authenticate_mode(self):
        # self._gui.root.switch_to(self._gui.root.screens[1])
        while not self._s.check_launch_phrase():
            self._s.speak(self._gui.root.ids['status_label'])
        print("You gained access")

    def _command_mode(self):
        while not self._s.check_close_phrase():
            # print(dir(self._action._screen_widgets()[0]))
            self._running.wait()
            self._s.speak(self._gui.root.ids['status_label'])

            if self._s.get_text() == "quit":
                self._gui.stop()
            
            resp = self._bot.message(self._s.get_text())
            if not resp:
                continue

            intents = resp['intents']
            entities = resp['entities']
            
            self._action.perform(intents, entities)
            # if(intents[0]['name'] == "weather"):
            #     day = self._widgets['mirror_clock'].diff_of_dates(entities['wit$datetime:datetime'][0]['value'][:10])
            #     self._widgets['weather'].request_weather(day)

            # if self._s.get_text() == "open settings":
            #     self._gui.show_settings()
            # elif self._s.get_text() == "tell me the weather":
            #     self._gui.root.ids["weather"].request_weather("London")
        self.run()


if __name__ == "__main__":
    interface = Controller()
