import os

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, ConfigParserProperty, DictProperty, NumericProperty

from controls import AbstractControls


class LoadDialog(FloatLayout):
    save_fn = ObjectProperty(None)
    cancel = ObjectProperty(None)
    video_input_path = ConfigParserProperty('/home/ziposc/Videos', 'ExercisorEditor', 'video_input_path', 'Exercisor')


class EditorControls(AbstractControls):

    exercises = DictProperty({}, force_dispatch=True, rebind=True)
    frame_indx = NumericProperty(0)

    def __init__(self, edit_actions, exercises, info_label, *args, **kwargs):
        self.info_label = info_label
        super().__init__(edit_actions, exercises, *args, **kwargs)

        self.user_touching_slider = False
        self.ids.prog_slider.bind(value=self.on_slider_value)

    def on_slider_value(self, instance, value):
        if self.user_touching_slider:
            self.actions['playback'].seek(value)

    def show_load_dialog(self):
        content = LoadDialog(save_fn=self.predict_from_video, cancel=self._dismiss_popup)
        self._popup = Popup(title='Load file', content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def _dismiss_popup(self):
        self._popup.dismiss()

    def predict_from_video(self, path, filename):
        self._dismiss_popup()
        if type(filename) == int:
            files = sorted(os.listdir(path))
            filename = files[filename]

        self.info_label.text = f'Predicting from the file: {filename[0]}'
        source = os.path.join(path, filename[0])
        self.actions['playback'].stop()
        self.actions['predict'].initialize(self.smpl_mode, source=source, save_exercise=True)
        self.actions['predict'].resume()
        self.frame_indx = 0

    def start_playback(self, exercise):
        if exercise in self.exercises.keys():
            self.info_label.text = f'Exercise playback: {exercise}'
            self.ids.prog_slider.max = len(self.exercises[exercise]) - 1
            self.actions['predict'].stop()
            self.actions['playback'].initialize(self.smpl_mode, self.exercises[exercise])
            self.actions['playback'].resume()

    def on_touch_down(self, touch):
        if self.actions['playback'].running and self.ids.prog_slider.collide_point(*touch.pos):
            # The touch has occurred inside the widgets area and on playback mode.
            self.user_touching_slider = True
            self.was_playing = not self.actions['playback'].paused
            self.actions['playback'].seek(self.frame_indx)

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self.user_touching_slider = False
        if hasattr(self, 'was_playing'):
            if self.actions['playback'].running and self.was_playing:
                self.actions['playback'].resume()
                self.was_playing = False
        return super().on_touch_up(touch)
