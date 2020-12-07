from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

import requests

from widgets.weather.weather import Weather
from widgets.clock.clock import MirrorClock
import config as cfg

Builder.load_file("widgets/weather/weather.kv")
Builder.load_file("widgets/clock/clock.kv")

class MainPage(FloatLayout):
    pass

class SmartMirrorApp(App):
    def build(self, **kwargs):
        return MainPage()

if __name__ == "__main__":
    # Window.fullscreen = 'auto'
    SmartMirrorApp().run()
