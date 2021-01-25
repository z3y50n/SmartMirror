from kivy.config import ConfigParser
import json
import os
import requests

from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, ConfigParserProperty
from kivy.uix.widget import Widget


CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(
    __file__, os.path.pardir, os.path.pardir, os.path.pardir)), "smartmirror.ini")

WEATHER_URL = "https://api.openweathermap.org/data/2.5/"


class Weather(Widget):
    _temperature = StringProperty("")
    _icon = StringProperty("")
    _description = StringProperty("")
    _api_key = ConfigParserProperty("", "WeatherAPI", "api_key", "Weather")
    _city_id = ConfigParserProperty("", "WeatherAPI", "city_id", "Weather")
    _city_name = ConfigParserProperty("", "WeatherAPI", "city_name", "Weather")
    _update_interval = ConfigParserProperty(
        "", "WeatherAPI", "update_interval", "Weather")
    _config = ConfigParser(name="Weather")

    def __init__(self, **kwargs):
        super(Weather, self).__init__(**kwargs)

        Clock.schedule_once(self._initialize_frame)

    def _initialize_frame(self, dt):
        self.update_config()
        self._get_weather(0)
        Clock.schedule_interval(
            self._get_weather, int(self._update_interval))

    def update_config(self):
        self._config.read(CONFIG_PATH)
        self._get_weather(0)

    def _get_weather(self, dt):
        try:
            if self._city_name:
                r = requests.get(
                    f"{WEATHER_URL}weather?q={self._city_name}&appid={self._api_key}&units=metric")
            else:
                r = requests.get(
                    f"{WEATHER_URL}weather?id={self._city_id}&appid={self._api_key}&units=metric")
            r = json.loads(r.text)

            self.ids['temp_label'].opacity = 1
            self.ids['temp_icon'].opacity = 1
            self._temperature = str(round(r['main']['temp']))
            self._icon = f"http://openweathermap.org/img/w/{r['weather'][0]['icon']}.png"
            self._description = f"{r['name']}: {r['weather'][0]['description']}"
        except:
            self.ids['temp_label'].opacity = 0
            self.ids['temp_icon'].opacity = 0
            self._description = "Could not fetch weather data"

    # TODO: Translate city name to lat&lon
    def request_weather(self, day):
        r = requests.get(
            f"{WEATHER_URL}onecall?lat=40.623341&lon=22.95369&units=metric&exclude=current,minutely,hourly&appid={self._api_key}")
        r = json.loads(r.text)
        print(json.dumps(r['daily'][day], indent=4))
        # print(json.dumps(r, indent=4))


if __name__ == "__main__":
    Builder.load_file("weather.kv")
    runTouchApp(Weather())
