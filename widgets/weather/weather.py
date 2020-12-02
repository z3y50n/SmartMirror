from kivy.uix.widget import Widget
from kivy.base import runTouchApp
from kivy.lang import Builder


class Weather(Widget):
    pass

if __name__ == "__main__":
    Builder.load_file("weather.kv")
    runTouchApp(Weather())