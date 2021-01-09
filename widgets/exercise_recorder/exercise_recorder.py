import os
import numpy as np

from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.clock import mainthread
from kivy.properties import ObjectProperty, ConfigParserProperty
from kivy.config import Config

from renderer import Renderer

import model_cfg
from log import logger
from model_threads import HMRThread, SMPLThread

Config.set('modules', 'monitor', '')
# Config.set('modules', 'showborder', '')
Config.set('graphics', 'width', '1080')
Config.set('graphics', 'height', '920')


class LoadDialog(FloatLayout):
    save_fn = ObjectProperty(None)
    cancel = ObjectProperty(None)
    video_input_path = ConfigParserProperty('/home/ziposc/Videos', 'exercise_editor', 'video_input_path', 'app')


class ExerciseRecorder(Widget):
    """
    """
    exercise_path = ConfigParserProperty('./widgets/exercise_recorder/exercise_data/',
                                         'exercise_editor', 'exercise_path', 'app')

    def __init__(self, **kwargs):
        super(ExerciseRecorder, self).__init__(**kwargs)
        self.renderer = Renderer(smpl_faces_path=model_cfg.smpl_faces_path,
                                 frame_label=self.ids.frame_label, mode_label=self.ids.mode_label)
        self.ids.renderer_layout.add_widget(self.renderer)

        # Load the saved exercises
        self.exercises = self.load_exercises(self.exercise_path)
        self.ids.playback_spin.values = self.exercises.keys()
        self.ids.playtest_spin.values = self.exercises.keys()

        self.mlthreads = {}
        self.mlthreads['hmr_thread'] = HMRThread(model_cfg, self.update_mesh, self.save_exercise)

        self.mlthreads['smpl_thread'] = SMPLThread(model_cfg.smpl_model_path, model_cfg.joint_type, self.update_mesh)

    def load_exercises(self, folder):
        files = os.listdir(folder)
        exercises = {os.path.splitext(file)[0]: np.load(os.path.join(folder, file)) for file in files}
        return exercises

    def playback(self, exercise):
        if exercise in self.exercises.keys():
            self.init_scene('smpl_mesh')
            self.mlthreads['smpl_thread'].exercise = self.exercises[exercise]
            self.mlthreads['smpl_thread'].resume()

    def playtest(self, exercise):
        if exercise in self.exercises.keys():
            self.playback(exercise)

    def init_scene(self, object):
        self.reset_ui()
        self.renderer.setup_scene(object)

    def render(self, object):
        self.init_scene(object)
        if object == 'smpl_mesh' or object == 'smpl_kpnts':
            self.mlthreads['hmr_thread'].resume()

    def show_load_dialog(self):
        content = LoadDialog(save_fn=self.predict_video, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def predict_video(self, path, filename):
        self.dismiss_popup()
        source = os.path.join(path, filename[0])
        self.mlthreads['hmr_thread'].capture = source
        self.mlthreads['hmr_thread'].save()
        self.render('smpl_mesh')
        logger.info(f'Predicting from the file: {filename[0]}')

    def save_exercise(self, filename, thetas):
        with open(f'{self.exercise_path}/{filename}.npy', 'w+b') as f:
            np.save(f, thetas)

    def dismiss_popup(self):
        self._popup.dismiss()

    @mainthread
    def update_mesh(self, new_verts=None, new_kpnts=None):
        if self.renderer.curr_obj == 'smpl_mesh':
            self.renderer.set_vertices(new_verts)
        elif self.renderer.curr_obj == 'smpl_kpnts':
            self.renderer.set_vertices(new_kpnts)

    def anim_mesh(self, btn_state, animation):
        if not hasattr(self, 'renderer'):
            raise UnboundLocalError('Renderer does not exist')

        state = True if btn_state == 'down' else False
        try:
            self.renderer.animate_mesh(animation, play=state)
        except UnboundLocalError:
            self.reset_buttons()

    def reset_ui(self):
        for thread in self.mlthreads.values():
            thread.pause()
        self.reset_buttons()
        self.renderer.reset_scene()

    def reset_buttons(self):
        self.ids.spin_1.text = 'Render'
        self.ids.playback_spin.text = 'Playback exercise'
        self.ids.playtest_spin.text = 'Playtest exercise'
        for i in range(1, 4):
            self.ids[f'tog_{i}'].state = 'normal'


if __name__ == '__main__':

    Builder.load_file('exercise_recorder.kv')
    runTouchApp(ExerciseRecorder())
