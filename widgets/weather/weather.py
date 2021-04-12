from kivy.config import ConfigParser
from datetime import datetime
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
CITIES_PATH = os.path.join(os.path.abspath(os.path.join(
    __file__, os.path.pardir, os.path.pardir, os.path.pardir)), "assets", "city.list.json")

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
    _lon = 0
    _lat = 0

    def __init__(self, **kwargs):
        super(Weather, self).__init__(**kwargs)

    def on_kv_post(self, dt):
        self.update_config()
        Clock.schedule_interval(
            self._get_weather, int(self._update_interval))

    def update_config(self):
        self._config.read(CONFIG_PATH)
        self._city_to_coord()
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

    def _diff_of_dates(self, s_date: str):
        today = datetime.now().date()
        s_date = datetime.strptime(s_date, DATE_FORMAT).date()
        diff = s_date - today
        print(f"Difference: {diff} Days")
        return diff.days

    def _diff_of_hours(self, date: str):
        days = self._diff_of_dates(date[:10])
        hour = int(date[11:13])
        now = datetime.now().hour
        diff = hour - now + days*24
        print(f"Difference: {diff} hours")
        return diff
        
    def _city_to_coord(self):
        with open(CITIES_PATH, "r") as f:
            cities = json.load(f)
        for city in cities:
            if city['name'].lower() == self._city_name.lower():
                self._lon = city['coord']['lon']
                self._lat = city['coord']['lat']

    def request_day(self, datetime="today"):
        if datetime == "today":
            day = 0
        else:
            day = self._diff_of_dates(datetime[:10])
            if day > 7 or day < 0:
                return [('speech', "I only know the weather for 7 days ahead")]

        r = requests.get(
            f"{WEATHER_URL}onecall?lat={self._lat}&lon={self._lon}&units=metric&exclude=current,minutely,hourly&appid={self._api_key}")
        
        r = json.loads(r.text)

        if day == 0:
            when = "today is"
        elif day == 1:
            when = "tommorrow will be"
        else:
            when = f"in {day} days will be"
        desc = r['daily'][day]['weather'][0]['main']
        temperature = r['daily'][day]['temp']['day']

        return [('speech', f"The weather {when} {desc} with {temperature} degrees Celcius")]
        # print(json.dumps(r['daily'][day], indent=4))

    def request_hour(self, datetime):
        hour = self._diff_of_hours(datetime)
        if hour > 47 or hour < 0:
            return [('speech', 'I only know the weather for 48 hours ahead')]

        r = requests.get(
            f"{WEATHER_URL}onecall?lat={self._lat}&lon={self._lon}&units=metric&exclude=current,minutely,daily&appid={self._api_key}")
        r = json.loads(r.text)
        
        when = "now is" if hour==0 else f"in {hour} hours will be"
        desc = r['hourly'][hour]['weather'][0]['main']
        temperature = r['hourly'][hour]['temp']

        return [('speech', f"The weather {when} {desc} with {temperature} degrees Celcius")]

    def request_location(self, location: str):
        r = requests.get(
                    f"{WEATHER_URL}weather?q={location}&appid={self._api_key}&units=metric")

        r = json.loads(r.text)
        text = f"The weather in {location} is {r['main']['temp']} degrees Celcius"

        return [("config", "weather", "city_name", location),
                ("speech", text)]

    def subscribe(self):
        return {
            "request_location": self.request_location,
            "request_hour": self.request_hour,
            "request_day": self.request_day
        }

if __name__ == "__main__":
    Builder.load_file("weather.kv")
    runTouchApp(Weather())
