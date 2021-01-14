import os
import numpy as np

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, ConfigParserProperty, DictProperty, NumericProperty

from log import logger


class LoadDialog(FloatLayout):
    save_fn = ObjectProperty(None)
    cancel = ObjectProperty(None)
    video_input_path = ConfigParserProperty('/home/ziposc/Videos', 'ExercisorEditor', 'video_input_path', 'Exercisor')


class EditorControls(BoxLayout):

    exercises = DictProperty({}, force_dispatch=True)
    frame_indx = NumericProperty(0)

    def __init__(self, edit_actions, exercises, info_label, *args, **kwargs):
        self.actions = edit_actions
        self.exercises = exercises
        self.info_label = info_label
        super().__init__(*args, **kwargs)

        self.smpl_mode = 'smpl_mesh'
        self.user_touching_slider = False
        self.ids.prog_slider.bind(value=self.on_slider_value)

    def on_slider_value(self, instance, value):
        if self.user_touching_slider:
            self.actions['playback'].seek(value)
            self.frame_indx = value

    def on_play(self, state):
        if state == 'down':
            for action in self.actions.values():
                if action.running:
                    action.resume()
                    return
            self.ids.playpause_btn.state = 'normal'
        else:
            for action in self.actions.values():
                if action.running:
                    action.pause()

    def show_load_dialog(self):
        content = LoadDialog(save_fn=self.predict_from_video, cancel=self._dismiss_popup)
        self._popup = Popup(title='Load file', content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def _dismiss_popup(self):
        self._popup.dismiss()

    def predict_from_video(self, path, filename):
        self._dismiss_popup()
        self.info_label.text = f'Predicting from the file: {filename[0]}'
        source = os.path.join(path, filename[0])
        self.actions['predict'].initialize(self.smpl_mode, source=source, saving=True)

        self.frame_indx = 0
        self.ids.playpause_btn.state = 'down'

    def start_playback(self, exercise):
        if exercise in self.exercises.keys():
            self.info_label.text = f'Exercise playback: {exercise}'
            self.ids.prog_slider.max = len(self.exercises[exercise]) - 1
            self.actions['playback'].initialize(self.smpl_mode, self.exercises[exercise])
            self.ids.playpause_btn.state = 'down'

    def set_smpl_mode(self, clicked_cb, is_active):
        if is_active:
            self.smpl_mode = f'smpl_{clicked_cb.value}'
            for action in self.actions.values():
                if action.running:
                    was_playing = not action.paused
                    action.initialize(self.smpl_mode)
                    if was_playing:
                        self.ids.playpause_btn.state = 'down'

    def reset_buttons(self):
        self.ids.play_spin.text = ''
        self.ids.playpause_btn.state = 'normal'

    def on_touch_down(self, touch):
        if self.actions['playback'].running and self.ids.prog_slider.collide_point(*touch.pos):
            # The touch has occurred inside the widgets area and on playback mode.
            self.user_touching_slider = True
            self.actions['playback'].seek(self.frame_indx)

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self.user_touching_slider = False
        if self.actions['playback'].running:
            if self.ids.playpause_btn.state == 'normal':
                self.actions['playback'].pause()
        return super().on_touch_up(touch)
