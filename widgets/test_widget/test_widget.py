from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

def install(manager):
    manager.add_widget(TestScreen())
    manager.add_widget(Button())

class TestScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
    
    def func(self):
        print("Hello world")

    def subscribe(self):
        return {
            "function": self.func
        }