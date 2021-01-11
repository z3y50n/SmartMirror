import os
import threading

from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.settings import SettingsWithSidebar

from main_controller import MainController
from settingsjson import settings_json, default_json
from widgets.clock.clock import MirrorClock
from widgets.weather.weather import Weather


WIDGET_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'widgets/')


class MainPage(FloatLayout):
    pass


class SmartMirrorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_start(self):
        controller = MainController(self)

    @mainthread
    def show_settings(self, command):
        if command == "open settings":
            self.open_settings()

    def on_config_change(self, config, section, key, value):
        for widget in self.root.ids.values():
            if hasattr(widget, "update_config"):
                widget.update_config()

    def build(self, **kwargs):
        for kv in os.listdir(WIDGET_PATH):
            Builder.load_file(os.path.join(WIDGET_PATH, kv, f"{kv}.kv"))
        self.settings_cls = SettingsWithSidebar
        return MainPage()

    def build_config(self, config):
        config.setdefaults("Speech", default_json["Speech"])
        config.setdefaults("WeatherAPI", default_json["WeatherAPI"])

    def build_settings(self, settings):
        settings.add_json_panel("Main Settings",
                                self.config,
                                data=settings_json)


if __name__ == "__main__":
    SmartMirrorApp().run()

