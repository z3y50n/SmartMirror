from datetime import datetime

from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

DATE_FORMAT = "%Y-%m-%d"


class MirrorClock(Widget):
    _hour = StringProperty("")
    _date = StringProperty("")

    def __init__(self, **kwargs):
        super(MirrorClock, self).__init__(**kwargs)
        self._update_time(0)
        Clock.schedule_interval(self._update_time, 1)

    def _update_time(self, dt):
        time = datetime.now()
        self._hour = f"{time.strftime('%H')}:{time.strftime('%M')}"
        self._date = f"{time.strftime('%A')} {time.strftime('%b')} {time.strftime('%d')} {time.strftime('%Y')}"


if __name__ == "__main__":
    Builder.load_file("clock.kv")
    runTouchApp(MirrorClock())
