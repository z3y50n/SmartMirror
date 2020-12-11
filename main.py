import os

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

from widgets.weather.weather import Weather
from widgets.clock.clock import MirrorClock

WIDGET_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'widgets/')


class MainPage(FloatLayout):
    pass


class SmartMirrorApp(App):
    def build(self, **kwargs):
        return MainPage()


if __name__ == "__main__":
    for kv in os.listdir(WIDGET_PATH):
        Builder.load_file(os.path.join(WIDGET_PATH, kv, f"{kv}.kv"))

    # Window.fullscreen = 'auto'
    SmartMirrorApp().run()
