import os
import multiprocessing
import threading

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.settings import SettingsWithSidebar

from interface import Interface
from settingsjson import settings_json, default_json
from widgets.clock.clock import MirrorClock
from widgets.weather.weather import Weather


WIDGET_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'widgets/')


class MainPage(FloatLayout):
    pass


class SmartMirrorApp(App):
    def build(self, **kwargs):
        self.settings_cls = SettingsWithSidebar
        return MainPage()

    def build_config(self, config):
        config.setdefaults("Speech", default_json["Speech"])
        config.setdefaults("WeatherAPI", default_json["WeatherAPI"])

    def build_settings(self, settings):
        settings.add_json_panel("Custom Settings",
                                self.config,
                                data=settings_json)


if __name__ == "__main__":
    for kv in os.listdir(WIDGET_PATH):
        Builder.load_file(os.path.join(WIDGET_PATH, kv, f"{kv}.kv"))

    # Window.fullscreen = 'auto'
    # ps1 = multiprocessing.Process(target = Interface().authenticate)
    gui = SmartMirrorApp()
    thread1 = threading.Thread(target=Interface(gui).authenticate)
    thread1.daemon = True
    thread1.start()
    gui.run()
    # ps1.terminate()
    # thread1.join()
