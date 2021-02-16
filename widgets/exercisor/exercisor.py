import os
from functools import partial
import numpy as np

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import ConfigParserProperty
from kivy.config import Config, ConfigParser

import model_cfg
from renderer import Renderer
from hmr_thread import HMRThread
from editor.smpl_thread import SMPLThread
from editor.editor_controls import EditorControls
from play.play_controls import PlayControls
from actions import PlaybackAction, PredictAction, PlayAction
from wit_wrapper import WitWrapper

# Config.set('modules', 'monitor', '')
# Config.set('modules', 'showborder', '')
Config.set('graphics', 'width', '1080')
Config.set('graphics', 'height', '920')


def install(manager):
    manager.add_widget(ExercisorScreen())


class ColorAdjustDialog(Widget):
    pass


class ExercisorScreen(Screen):
    pass


class Exercisor(BoxLayout):
    """
    """
    config = ConfigParser('Exercisor')
    exercises_path = ConfigParserProperty('./widgets/exercisor/exercise_data/',
                                          'Exercisor', 'exercises_path', 'Exercisor')
    obj_mesh_path = ConfigParserProperty('./widgets/exercisor/play/monkey.obj', 'Exercisor', 'obj_mesh_path',
                                         'Exercisor')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load the kv files
        path = os.path.dirname(os.path.abspath(__file__))
        for elem in ('play', 'editor'):
            Builder.load_file(os.path.join(path, elem, f'{elem}_controls.kv'))

        Builder.load_file(os.path.join(path, 'controls.kv'))
        self.mlthreads = {}
        self.mlthreads['hmr'] = HMRThread(model_cfg, self.save_exercise)
        self.mlthreads['smpl'] = SMPLThread(model_cfg.smpl_model_path, model_cfg.joint_type)

    def on_kv_post(self, base_widget):

        # Load the saved exercises
        self.exercises = self._load_exercises(self.exercises_path)

        paths = {
            'smpl_faces_path': model_cfg.smpl_faces_path,
            'obj_mesh_path': self.obj_mesh_path,
        }
        renderer = Renderer(**paths)
        self.ids.renderer_layout.add_widget(renderer)
        play_renderers = [renderer, Renderer(**paths), Renderer(**paths)]
        self.actions = {
            'playback': PlaybackAction(self.mlthreads['smpl'], renderer),
            'predict': PredictAction(self.mlthreads['hmr'], renderer),
            'play': PlayAction(self.mlthreads, play_renderers)
        }

        self.color_adjust_dialog = ColorAdjustDialog()
        self.color_adjust_dialog.bind(diffuse_light_color=partial(self.on_color_change, 'diffuse'))
        self.color_adjust_dialog.bind(object_color=partial(self.on_color_change, 'object'))

        self.change_control('normal')  # Displays the control buttons

    def update_config(self):
        # Documentation for settings
        # self.config.read('config_path')
        pass

    def subscribe(self):
        # Documentation for wit.ai integration
        wit_wrap = WitWrapper(self)
        exported_functions = wit_wrap.export_functions()

        return exported_functions

    def change_control(self, state):
        """ Change the buttons at the bottom of the window """
        self.ids.ctrl_btn.state = state
        self.ids.controls_layout.clear_widgets()
        if state == 'down':
            edit_actions = {key: self.actions[key] for key in ('playback', 'predict')}
            self.controls = EditorControls(edit_actions, self.exercises, self.ids.info_label)
        else:
            play_actions = {key: self.actions[key] for key in ('play', 'predict')}
            self.controls = PlayControls(play_actions, self.exercises, self.ids.info_label)

        for action in self.actions.values():
            action.stop()
        self.ids.info_label.text = 'Waiting to choose an exercise..'
        self.ids.controls_layout.add_widget(self.controls)

    def toggle_color_adjust(self, state):
        if state == 'down':
            self.ids.renderer_layout.add_widget(self.color_adjust_dialog)
        else:
            self.ids.renderer_layout.remove_widget(self.color_adjust_dialog)

    def on_color_change(self, color_type, _, new_color):
        for renderer in self.ids.renderer_layout.walk(restrict=True):
            if type(renderer) == Renderer:
                if color_type == 'object':
                    renderer.canvas['object_color'] = new_color
                elif color_type == 'diffuse':
                    renderer.canvas['diffuse_light'] = new_color

    def _load_exercises(self, folder):
        files = os.listdir(folder)
        exercises = {os.path.splitext(file)[0]: np.load(os.path.join(folder, file)) for file in files}
        return exercises

    def save_exercise(self, filename, thetas):
        """ Save the thetas of the exercise and update the list of available exercises

        Parameters
        ----------
        filename: str
            The name of the file to will be saved
        thetas: list of lists (N x 82)
            The 82 theta parameters of the smpl model for each frame
        """
        with open(f'{self.exercises_path}/{filename}.npy', 'w+b') as f:
            np.save(f, thetas)

        self.exercises = self._load_exercises(self.exercises_path)

        self.ids.info_label.text = f'Exercise {filename} has been saved to {self.exercises_path}'
        for action in self.actions.values():
            action.stop()

    def anim_mesh(self, btn_state, animation):
        if not hasattr(self, 'renderer'):
            raise UnboundLocalError('Renderer does not exist')

        state = True if btn_state == 'down' else False
        try:
            self.renderer.animate_mesh(animation, play=state)
        except UnboundLocalError:
            self.reset_buttons()

    def stop_threads_exec(self):
        for thread in self.mlthreads.values():
            thread.resume()
            thread.stop_exec()

    @property
    def controls(self):
        return self._controls

    @controls.setter
    def controls(self, new_controls):
        self._controls = new_controls
        for action in self.actions.values():
            action.controls = self._controls

    @property
    def exercises(self):
        return self._exercises

    @exercises.setter
    def exercises(self, new_exercises):
        self._exercises = new_exercises
        if hasattr(self, 'controls'):
            self.controls.exercises = self._exercises


class ExercisorApp(App):

    def build(self):
        return ExercisorScreen()

    def on_stop(self):
        self.root.ids.exercisor.stop_threads_exec()


if __name__ == '__main__':

    ExercisorApp().run()
