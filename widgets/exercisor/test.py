
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.slider import Slider

Config.set('modules', 'monitor', '')
# Config.set('modules', 'showborder', '')
Config.set('graphics', 'width', '1080')
Config.set('graphics', 'height', '920')

Builder.load_string("""
<Exercisor>:
    progress: progress
    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        Slider:
            id: progress
            min: 0
            max: 100
            step: 1
            value_track: True
            value_track_color: 1, 0, 0, 1
        Label:
            text: str(progress.value)
""")


class Exercisor(Widget):
    """
    """
    progress = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        s = Slider(value_track=True, value_track_color=[1, 0, 0, 1])


if __name__ == '__main__':
    runTouchApp(Exercisor())
