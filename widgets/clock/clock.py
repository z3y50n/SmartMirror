from kivy.uix.widget import Widget
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty

import datetime


class MirrorClock(Widget):
    hour = StringProperty("")
    date = StringProperty("")

    def __init__(self, **kwargs):
        super(MirrorClock, self).__init__(**kwargs)
        self.update_time(0)
        Clock.schedule_interval(self.update_time, 1)

    def update_time(self, dt):
        time = datetime.datetime.now()
        self.hour = f"{time.strftime('%H')}:{time.strftime('%M')}"
        self.date = f"{time.strftime('%A')} {time.strftime('%b')} {time.strftime('%d')} {time.strftime('%Y')}"


if __name__ == "__main__":
    Builder.load_file("clock.kv")
    runTouchApp(MirrorClock())
