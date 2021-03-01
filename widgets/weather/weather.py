from kivy.config import ConfigParser
from datetime import datetime
import json
import os
import requests
import time

from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, ConfigParserProperty
from kivy.uix.widget import Widget


CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(
    __file__, os.path.pardir, os.path.pardir, os.path.pardir)), "smartmirror.ini")

WEATHER_URL = "https://api.openweathermap.org/data/2.5/"
DATE_FORMAT = "%Y-%m-%d"


class Weather(Widget):
    _temperature = StringProperty("")
    _icon = StringProperty("")
    _description = StringProperty("")
    _api_key = ConfigParserProperty("", "weather", "api_key", "Weather")
    _city_id = ConfigParserProperty("", "weather", "city_id", "Weather")
    _city_name = ConfigParserProperty("", "weather", "city_name", "Weather")
    _update_interval = ConfigParserProperty(
        "", "weather", "update_interval", "Weather")
    _config = ConfigParser(name="Weather")

    def __init__(self, **kwargs):
        super(Weather, self).__init__(**kwargs)

    def on_kv_post(self, dt):
        self.update_config()
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

    def request_day(self, datetime):
        """TODO: Translate city name to lat&lon"""
        day = self._diff_of_dates(datetime[:10])
        if day > 7 or day < 0:
            print("I only know the weather for 7 days ahead :(")
            return

        r = requests.get(
            f"{WEATHER_URL}onecall?lat=40.623341&lon=22.95369&units=metric&exclude=current,minutely,hourly&appid={self._api_key}")
        r = json.loads(r.text)
        print(json.dumps(r['daily'][day], indent=4))
        # print(json.dumps(r, indent=4))
        temperature = 10
        return ('speech', f"The weather tomorrow will be sunny with {temperature} degrees Celcius")

    def _diff_of_dates(self, s_date: str):
        today = datetime.now().date()
        s_date = datetime.strptime(s_date, DATE_FORMAT).date()
        diff = s_date - today
        print(f"Difference: {diff} Days")
        return diff.days

    def request_hour(self, datetime):
        r = requests.get(
            f"{WEATHER_URL}onecall?lat=40.623341&lon=22.95369&units=metric&exclude=current,minutely,daily&appid={self._api_key}")
        r = json.loads(r.text)
        hour = self._diff_of_hours(datetime)
        print(json.dumps(r['hourly'][hour], indent=4))
        return

    def _diff_of_hours(self, date: str):
        days = self._diff_of_dates(date[:10])
        hour = int(date[11:13])
        now = datetime.now().hour
        diff = hour - now + days*24
        print(f"Difference: {diff} hours")
        return diff
        
    def request_city(self, location: str):
        return ("config", "WeatherAPI", "city_name", location)

    def subscribe(self):
        return {
            "request_city": self.request_city,
            "request_hour": self.request_hour,
            "request_day": self.request_day
        }

if __name__ == "__main__":
    Builder.load_file("weather.kv")
    runTouchApp(Weather())
