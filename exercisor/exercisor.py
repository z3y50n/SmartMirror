import os
from functools import partial
import numpy as np

from kivy.app import App
from kivy.uix.widget import Widget
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
from log import logger

# Config.set('modules', 'monitor', '')
# Config.set('modules', 'showborder', '')
Config.set('graphics', 'width', '1080')
Config.set('graphics', 'height', '920')


def install(manager):
    """ Create and pass the Exercisor Widget to SmartMirror's screen manager """
    manager.add_widget(ExercisorScreen())


class ColorAdjustDialog(Widget):
    """ The dialog to  """
    pass


class ExercisorScreen(Screen):
    """ The main screen of the Exercisor Widget """
    config = ConfigParser('Exercisor')
    exercises_path = ConfigParserProperty('./exercisor/exercise_data/',
                                          'Exercisor', 'exercises_path', 'Exercisor')
    obj_mesh_path = ConfigParserProperty('./exercisor/play/monkey.obj', 'Exercisor', 'obj_mesh_path',
                                         'Exercisor')

    def __init__(self, **kwargs):
        # Load the kv files
        path = os.path.dirname(os.path.abspath(__file__))
        Builder.load_file(os.path.join(path, 'controls.kv'))
        Builder.load_file(os.path.join(path, 'play', 'player.kv'))
        Builder.load_file(os.path.join(path, 'editor', 'editor.kv'))

        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):

        # Create the SMPL and HMR threads
        self.mlthreads = {}
        self.mlthreads['hmr'] = HMRThread(model_cfg, self.save_exercise)
        self.mlthreads['smpl'] = SMPLThread(model_cfg.smpl_model_path, model_cfg.joint_type)

        # Create the renderer widgets for the SMPL and HMR treads and for the error vectors
        kwargs = {
            'smpl_faces_path': model_cfg.smpl_faces_path,
            'keypoints_spec': model_cfg.keypoints_spec,
            'obj_mesh_path': self.obj_mesh_path,
        }
        renderers = [Renderer(**kwargs), Renderer(**kwargs), Renderer(**kwargs)]
        for rend in renderers:
            self.ids.renderer_layout.add_widget(rend)

        # Create the color adjustment dialog and bind the color change function
        self.color_adjust_dialog = ColorAdjustDialog()
        self.color_adjust_dialog.bind(diffuse_light_color=partial(self.on_color_change, 'diffuse'))
        self.color_adjust_dialog.bind(object_color=partial(self.on_color_change, 'object'))
        self.color_adjust_dialog.object_color = (0.95, 0.85, 0.95)
        self.color_adjust_dialog.diffuse_light_color = (0.9, 0.9, 0.9)

        # Create the controlling classes of the thread's and renderers' state
        self.actions = {
            'playback': PlaybackAction(self.mlthreads['smpl'], renderers[0], model_cfg.keypoints_spec),
            'predict': PredictAction(self.mlthreads['hmr'], renderers[0]),
            'play': PlayAction(self.mlthreads, renderers)
        }

        # Load the saved exercises and apply smoothing
        self.exercises = self._load_exercises(self.exercises_path)
        for name, exercise in self.exercises.items():
            self.exercises[name] = self._smooth_thetas(exercise, 10)

        self.change_control('normal')  # Displays the control buttons

    def update_config(self):
        # Documentation for settings
        # self.config.read('config_path')
        pass

    def subscribe(self):
        """ Export the functions for the wit.ai integration """
        wit_wrap = WitWrapper(self)
        exported_functions = wit_wrap.export_functions()

        return exported_functions

    def change_control(self, state):
        """ Change the buttons at the bottom center of the window """
        self.ids.ctrl_btn.state = state
        if state == 'down':
            edit_actions = {key: self.actions[key] for key in ('playback', 'predict')}
            self.controls = EditorControls(edit_actions, self.exercises, self.ids.info_label)
        else:
            play_actions = {key: self.actions[key] for key in ('play', 'predict')}
            self.controls = PlayControls(play_actions, self.exercises, self.ids.info_label)

    def _stop_actions(self):
        for action in self.actions.values():
            action.stop()

    def toggle_color_adjust(self, state):
        """ Toggle the ColorAdjustment dialog """
        if state == 'down':
            self.ids.renderer_layout.add_widget(self.color_adjust_dialog)
        else:
            self.ids.renderer_layout.remove_widget(self.color_adjust_dialog)

    def on_color_change(self, color_type, _, new_color):
        """ Change the color of the rendered meshes.

        Parameters
        ----------
        color_type : {'object', 'diffuse'}
            Specify the type of the color to change, either the color of the object or the diffuse lighting color
        new_color : tuple of floats in range [0, 1]
            The new rgb values for the specified `color_type`
        """
        for renderer in self.ids.renderer_layout.walk(restrict=True):
            if type(renderer) == Renderer:
                if color_type == 'object':
                    renderer.canvas['object_color'] = new_color
                elif color_type == 'diffuse':
                    renderer.canvas['diffuse_light'] = new_color

    def _load_exercises(self, folder):
        """ Load the exercises from the specified folder """
        if not os.path.isdir(folder):
            logger.warning(f'The path `{folder}` does not exist or it is not a folder.')
            return
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
        self._stop_actions()

    def _smooth_thetas(self, thetas, window):
        """ Smooth the frames of the saved exercised via moving average on the thetas

        Parameters
        ----------
        thetas: array_like (N x 82)
            The 82 SMPL parameters for each of the N frames
        window: int
            The sample window of the moving average
        """
        left = int(window / 2)
        right = int(window / 2) if window % 2 == 0 else int(window / 2) + 1
        for nf in range(0, thetas.shape[0]):
            for kid in range(0, 72, 3):
                lb = nf - left if nf - left >= 0 else 0
                rb = nf + right if nf + right < thetas.shape[0] else thetas.shape[0] - 1
                thetas[nf, kid: kid + 3] = thetas[lb: rb, kid: kid + 3].mean(axis=0)

        return thetas

    @property
    def controls(self):
        """ The BoxLayout widget that holds the buttons at the bottom center of the screen.

        When set, update the :attr: controls of each of the :class: AbstractAction.
        """
        return self._controls

    @controls.setter
    def controls(self, new_controls):
        self._controls = new_controls
        self._stop_actions()
        self.ids.controls_layout.clear_widgets()

        for action in self.actions.values():
            action.controls = self._controls

        self.ids.info_label.text = 'Waiting to choose an exercise..'
        self.ids.controls_layout.add_widget(self._controls)

    @property
    def exercises(self):
        """ The dictionary {'name': thetas} that holds for each exercise its name and its saved thetas.

        When set, updates the :attr: exercises of the :class: AbstractControls.
        """
        return self._exercises

    @exercises.setter
    def exercises(self, new_exercises):
        self._exercises = new_exercises
        if hasattr(self, 'controls'):
            self.controls.exercises = self._exercises


class ExercisorApp(App):

    def build(self):
        return ExercisorScreen()


if __name__ == '__main__':

    ExercisorApp().run()
