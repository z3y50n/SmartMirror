import os

from kivy.properties import ObjectProperty, ConfigParserProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup

from controls import AbstractControls
from editor.keypoint_editor import KeypointEditForm


class LoadDialog(FloatLayout):
    """A video file chooser dialog.

    The user can select a video file which will be used for predicting the groundtruth exercise data.

    Attributes
    -----------
    save_from_video : `kivy.properties.ObjectProperty`
        Initiates the `predict` action.
    cancel : `kivy.properties.ObjectProperty`
        Closes the displayed dialog.
    video_input_path : `kivy.properties.ConfigParserProperty`
        The default starting directory of the dialog.
    """
    save_from_video = ObjectProperty(None)
    cancel = ObjectProperty(None)
    video_input_path = ConfigParserProperty('/home/ziposc/Videos', 'ExercisorEditor', 'video_input_path', 'Exercisor')


class EditorControls(AbstractControls):
    """The Editor screen control buttons.

    The Editor buttons at the bottom center contain
        - a button, for choosing a saved exercise.
        - a play/pause button.
        - a slider, displaying and controlling the current frame of the playbacked exercise.
        - a toggle, choosing the display mode: mesh or keypoints.
        - a button, for opening the `LoadDialog`.

    Moreover, the Editor control buttons include the dialogs
        - LoadDialog, to choose a video file and save the groundtruth exercise.
        - KeypointEditForm, to edit the keypoints of the playbacked exercise.

    Attributes
    ----------
    frame_indx : `kivy.properties.NumericProperty`
        The current frame of the playbacked exercise.
    user_touching_slider : `bool`
        Whether the user is currently touching the slider or not.
    """

    frame_indx = NumericProperty(0)

    def __init__(self, edit_actions, info_label, *args, **kwargs):
        super().__init__(edit_actions, info_label, *args, **kwargs)

        self.user_touching_slider = False
        self.ids.prog_slider.bind(value=self.on_slider_value)

    def on_frame_indx(self, instance, value):
        try:
            self.kpnt_edit_form.frame_indx = int(value)
        except AttributeError:
            pass

    def on_slider_value(self, instance, value):
        """ Binding when the user is using the slider to set the time point of the exercise. """
        if self.user_touching_slider:
            self.actions['playback'].seek(value)

    def show_load_dialog(self):
        """ Display a dialog to choose and load an exercise from video. """
        content = LoadDialog(save_from_video=self.predict_from_video, cancel=self.dismiss_popup)
        self._popup = Popup(title='Load file', content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def dismiss_popup(self):
        """ Close the load dialog """
        self._popup.dismiss()

    def predict_from_video(self, path, filename):
        """ Start the `predict` action to save the results of an exercise video as groundtruth exercise. """
        self.dismiss_popup()
        if type(filename) == int:
            files = sorted(os.listdir(path))
            filename = files[filename]

        self.info_label.text = f'Predicting from the file: {filename[0]}'
        source = os.path.join(path, filename[0])
        self.actions['playback'].stop()
        self.actions['predict'].initialize(self.smpl_mode, source=source, save_exercise=True)
        self.frame_indx = 0

    def start_exercise(self, exercise_name: str):
        """ Start the `playback` action to playback a saved exercise.
        
        Parameters
        ----------
        exercise : `str`
            The name of the exercise to be played.
        """
        if exercise_name in self.exercises.keys():
            super().start_exercise(exercise_name)
            self.ids.prog_slider.max = len(self.exercises[exercise_name]) - 1
            self.actions['predict'].stop()
            self.actions['playback'].initialize(self.smpl_mode, self.exercises[exercise_name])

    def update(self, exercise_controller):
        super().update(exercise_controller)
        if self.actions['playback'].running:
            self.actions['playback'].exercise = self.exercises[exercise_controller.current_exercise]

    def display_kpnt_edit_form(self, kpnt_name: str, keypoints_spec):
        """ Display a popup with the keypoint edit dialog. """
        try:
            self.kpnt_edit_form.set_curr_keypoint(kpnt_name)
        except AttributeError:
            self.kpnt_edit_form = KeypointEditForm(keypoints_spec=keypoints_spec, curr_kpnt=kpnt_name,
                                                   setup_highlight=self.actions['playback'].renderer.setup_highlight,
                                                   frame_indx=self.frame_indx,
                                                   exercise_controller=self.exercise_controller,
                                                   save_kpnt_options=self.save_kpnt_options,
                                                   cancel_form=self.dismiss_kpnt_edit_form)
            self.parent.parent.parent.add_widget(self.kpnt_edit_form)

    def save_kpnt_options(self):
        # TODO: save rules
        self.dismiss_kpnt_edit_form()

    def dismiss_kpnt_edit_form(self):
        try:
            self.parent.parent.parent.remove_widget(self.kpnt_edit_form)
            del(self.kpnt_edit_form)
        except AttributeError:
            pass
        self.actions['playback'].renderer.reset_highlight()

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

    def reset_ui(self):
        self.dismiss_kpnt_edit_form()
        super().reset_ui()
