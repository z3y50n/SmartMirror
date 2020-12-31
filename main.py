import os

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.settings import SettingsWithSidebar

from interface import Interface
from settingsjson import settings_json
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
        config.setdefaults("Speech", {
            "launch_phrase": "mirror mirror on the wall",
            "close_phrase": "thank you mirror"
        })
        config.setdefaults("WeatherAPI", {
            "api_key": "26be86d9cd70b50cb932ddf568ebac0c",
            "city_id": "8133841",
            "update_interval": 1800
        })

    def build_settings(self, settings):
        settings.add_json_panel("Custom Settings",
                                self.config,
                                data=settings_json)


if __name__ == "__main__":
    for kv in os.listdir(WIDGET_PATH):
        Builder.load_file(os.path.join(WIDGET_PATH, kv, f"{kv}.kv"))

    # Window.fullscreen = 'auto'
    SmartMirrorApp().run()


