
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty


class PlayControls(GridLayout):

    play_spin = ObjectProperty(None)

    def __init__(self, exercises, init_scene, resume_threads, reset_ui, *args, **kwargs):
        self.exercises = exercises
        self.init_scene = init_scene
        self.resume_threads = resume_threads
        self.reset_ui = reset_ui
        super().__init__(*args, **kwargs)

    def reset_buttons(self):
        pass
