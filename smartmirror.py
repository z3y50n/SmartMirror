import os
import random
import json
import importlib

from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar

from modules.controller import Controller
from modules.basedir import BASEDIR
from mirror_settings import settings_json, default_json, WELCOME_MESSAGES, KIVY_FONTS


WIDGET_PATH = os.path.join(BASEDIR, "widgets/")

WIDGETS = []  # Store all imported widgets

# Import every module located in widget folder
for widget in os.listdir(WIDGET_PATH):
    if os.path.exists(
        os.path.join(WIDGET_PATH, widget, "__init__.py")
    ) and os.path.exists(os.path.join(WIDGET_PATH, widget, f"{widget}.py")):
        WIDGETS.append(importlib.import_module(f"widgets.{widget}.{widget}"))

for font in KIVY_FONTS:
    LabelBase.register(**font)


class MainPage(ScreenManager):
    _welcome = StringProperty("")

    def __init__(self, **kwargs):
        super(MainPage, self).__init__(**kwargs)
        self._welcome = random.choice(WELCOME_MESSAGES)
        self.installer()
        print(self.children)
        self.current = "exercise screen"

    def add_widget(self, screen):
        """Overload add_widget function for extra security"""
        if isinstance(screen, Screen):
            super(MainPage, self).add_widget(screen)

    def installer(self):
        """Call installers of every imported widget

        Probably not very secure...
        """
        for widget in WIDGETS:
            if hasattr(widget, "install"):
                widget.install(self)


class SmartMirrorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.controller = None

    def on_start(self):
        self.controller = Controller(self)

    def build(self, **kwargs):
        for kv in os.listdir(WIDGET_PATH):
            Builder.load_file(os.path.join(WIDGET_PATH, kv, f"{kv}.kv"))
        self.settings_cls = SettingsWithSidebar
        Window.borderless = True
        return MainPage()

    def subscribe(self):
        return {"change_screen": self.change_screen}

    def change_screen(self, screen_name):
        if self.root.has_screen(screen_name):
            self.root.current = screen_name
            return ["update"]
        print("No screen with that name")
        return

    @mainthread
    def show_settings(self):
        self.open_settings()

    @mainthread
    def on_config_change(self, config, section, key, value):
        for widget in self.root.ids.values():
            if hasattr(widget, "update_config"):
                widget.update_config()

    def build_config(self, config):
        config.setdefaults("Wit", default_json["Wit"])
        config.setdefaults("Speech", default_json["Speech"])

        # Get default values from every widget
        for widget in os.listdir(WIDGET_PATH):
            if os.path.exists(os.path.join(WIDGET_PATH, widget, "settings.json")):
                with open(os.path.join(WIDGET_PATH, widget, "settings.json")) as f:
                    default = json.load(f)["default_json"]
                    config.setdefaults(widget, default)

    def build_settings(self, settings):
        settings.add_json_panel("Main Settings", self.config, data=settings_json)

        # Create a panel for every widget that has settings.json file
        for widget in os.listdir(WIDGET_PATH):
            if os.path.exists(os.path.join(WIDGET_PATH, widget, "settings.json")):
                with open(os.path.join(WIDGET_PATH, widget, "settings.json")) as f:
                    temp_settings = json.dumps(json.load(f)["settings_json"])
                    settings.add_json_panel(widget, self.config, data=temp_settings)


if __name__ == "__main__":
    SmartMirrorApp().run()
