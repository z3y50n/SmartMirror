import os
import numpy as np

from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.clock import mainthread
from kivy.properties import ObjectProperty, ConfigParserProperty
from kivy.config import Config, ConfigParser

import model_cfg
from renderer import Renderer
from log import logger
from hmr_thread import HMRThread
from editor.smpl_thread import SMPLThread
from editor.editor_controls import EditorControls
from play.play_controls import PlayControls
from actions import PlaybackAction, PredictAction, PlayAction

# Config.set('modules', 'monitor', '')
# Config.set('modules', 'showborder', '')
Config.set('graphics', 'width', '1080')
Config.set('graphics', 'height', '920')


class Exercisor(Widget):
    """
    """
    config = ConfigParser('Exercisor')
    exercises_path = ConfigParserProperty('./widgets/exercisor/exercise_data/',
                                          'Exercisor', 'exercises_path', 'Exercisor')
    mesh_path = ConfigParserProperty('./widgets/exercisor/play/monkey.obj', 'Exercisor', 'mesh_path', 'Exercisor')

    ctrl_btn = ObjectProperty(None)
    renderer_layout = ObjectProperty(None)
    controls_layout = ObjectProperty(None)
    info_label = ObjectProperty(None)
    frame_lab = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.renderer = Renderer(smpl_faces_path=model_cfg.smpl_faces_path, frame_label=self.frame_lab,
                                 mesh_path=self.mesh_path)
        self.renderer_layout.add_widget(self.renderer)

        # Load the kv files
        path = os.path.dirname(os.path.abspath(__file__))
        for elem in ('play', 'editor'):
            Builder.load_file(os.path.join(path, elem, f'{elem}_controls.kv'))

        # Load the saved exercises
        self.exercises = self._load_exercises(self.exercises_path)

        self.mlthreads = {}
        self.mlthreads['hmr_thread'] = HMRThread(model_cfg, self.update_mesh, self.save_exercise)
        self.mlthreads['smpl_thread'] = SMPLThread(model_cfg.smpl_model_path, model_cfg.joint_type, self.update_mesh)

        self.actions = {
            'playback': PlaybackAction(self.mlthreads['smpl_thread'], self.init_scene, self.reset_ui),
            'predict': PredictAction(self.mlthreads['hmr_thread'], self.init_scene, self.reset_ui),
            'play': PlayAction(self.mlthreads)
        }

        self.change_control('normal')

    def update_config(self):
        # self.config.read('config_path')
        pass

    def change_control(self, state):
        self.controls_layout.clear_widgets()
        if state == 'down':
            edit_actions = {key: self.actions[key] for key in ['playback', 'predict']}
            self.controls = EditorControls(edit_actions, self.exercises, self.info_label)
        else:
            self.controls = PlayControls(self.exercises, self.init_scene,
                                         self.resume_threads, self.reset_ui)

        self.reset_ui()
        self.info_label.text = 'Waiting to choose an exercise..'
        self.controls_layout.add_widget(self.controls)

    def _load_exercises(self, folder):
        files = os.listdir(folder)
        exercises = {os.path.splitext(file)[0]: np.load(os.path.join(folder, file)) for file in files}
        return exercises

    def render(self, object):
        self.reset_ui()
        self.init_scene(object)
        if object == 'smpl_mesh' or object == 'smpl_kpnts':
            self.mlthreads['hmr_thread'].resume()

    def init_scene(self, object):
        self.renderer.setup_scene(object)

    def resume_threads(self, names, source=None, saving=False):
        if 'hmr' in names:
            if source is not None:
                self.mlthreads['hmr_thread'].capture = source
                self.info_label.text = f'Currently playing: {os.path.split(source)[-1]}'
            if saving:
                self.mlthreads['hmr_thread'].save()
            self.mlthreads['hmr_thread'].resume()
        if 'smpl' in names:
            if source is not None:
                self.mlthreads['smpl_thread'].exercise = self.exercises[source]
                self.info_label.text = f'Currently playing: {source}'
            self.mlthreads['smpl_thread'].resume()

    @mainthread
    def update_mesh(self, new_verts=None, new_kpnts=None, frame_index=None):
        if self.renderer.curr_obj == 'smpl_mesh':
            self.renderer.set_vertices(new_verts)
        elif self.renderer.curr_obj == 'smpl_kpnts':
            self.renderer.set_vertices(new_kpnts)

        if self.actions['playback'].running and frame_index is not None:
            # self.actions['playback'].update_frame()
            if not self.controls.user_touching_slider:
                self.controls.frame_indx = frame_index

    def save_exercise(self, filename, thetas):
        with open(f'{self.exercises_path}/{filename}.npy', 'w+b') as f:
            np.save(f, thetas)
        self.exercises = self._load_exercises(self.exercises_path)
        self.info_label.text = f'Exercise {filename} has been saved to {self.exercises_path}'
        self.reset_ui()

    def anim_mesh(self, btn_state, animation):
        if not hasattr(self, 'renderer'):
            raise UnboundLocalError('Renderer does not exist')

        state = True if btn_state == 'down' else False
        try:
            self.renderer.animate_mesh(animation, play=state)
        except UnboundLocalError:
            self.reset_buttons()

    def reset_ui(self):
        self.actions['predict'].stop()
        self.actions['playback'].stop()
        self.controls.reset_buttons()
        self.renderer.reset_scene()

    @property
    def exercises(self):
        return self._exercises

    @exercises.setter
    def exercises(self, new_exercises):
        self._exercises = new_exercises
        if hasattr(self, 'controls'):
            self.controls.exercises = self._exercises


if __name__ == '__main__':

    Builder.load_file('exercisor.kv')
    runTouchApp(Exercisor())
