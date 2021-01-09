from configparser import ConfigParser
import json
import os
import requests

from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.widget import Widget


CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(
    __file__, os.path.pardir, os.path.pardir, os.path.pardir)), "smartmirror.ini")


class Weather(Widget):
    temperature = StringProperty("")
    icon = StringProperty("")
    description = StringProperty("")

    def __init__(self, **kwargs):
        super(Weather, self).__init__(**kwargs)

        config = ConfigParser()
        config.read(CONFIG_PATH)
        self.cfg = config['WeatherAPI']

        self.get_weather(0)

        # Update Temperature Every Set Interval
        Clock.schedule_interval(
            self.get_weather, int(self.cfg['update_interval']))

    def get_weather(self, dt):
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?id={self.cfg['city_id']}&appid={self.cfg['api_key']}&units=metric")
        r = json.loads(r.text)

        self.temperature = str(round(r['main']['temp']))
        self.icon = f"http://openweathermap.org/img/w/{r['weather'][0]['icon']}.png"
        self.description = f"{r['name']}: {r['weather'][0]['description']}"


if __name__ == "__main__":
    print(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "config.json"))
    Builder.load_file("weather.kv")
    runTouchApp(Weather())
