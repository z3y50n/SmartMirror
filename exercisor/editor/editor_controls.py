import os

from kivy.properties import ObjectProperty, ConfigParserProperty, NumericProperty, StringProperty, ListProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup

from controls import AbstractControls


class LoadDialog(FloatLayout):
    """A file chooser dialog.

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


class KeypointEditForm(FloatLayout):
    """A form to edit the movement of a selected keypoint from the rendered mesh.

    Attributes
    ----------
    highlight_keypoint : `callable`
        A function that highlights the currently selected keypoint.
    name : `kivy.properties.StringProperty`
        The name of the selected keypoint.
    keypoints_spec : `kivy.properties.ListProperty`
        A list of dictionaries containing the SMPL keypoints' specifications.
    save_kpnt_options : `kivy.properties.ObjectProperty`
        A function to save the editted options of the keypoint.
    cancel : `kivy.properties.ObjectProperty`
        A function to close the form.
    prev_kpnt : `kivy.properties.StringProperty`
        The name of the previous keypoint.
    next_kpnt : `kivy.properties.StringProperty`
        The name of the next keypoint.
    """
    name = StringProperty('Unknown', rebind=True)
    keypoints_spec = ListProperty([])
    save_kpnt_options = ObjectProperty(None)
    cancel = ObjectProperty(None)
    prev_kpnt = StringProperty('', rebind=True)
    next_kpnt = StringProperty('', rebind=True)

    def __init__(self, setup_highlight, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_highlight = setup_highlight
        self.kpnt_indx = next(i for i, kpnt in enumerate(self.keypoints_spec) if kpnt['name'] == self.name)

    def cycle_prev(self):
        self.kpnt_indx = (self.kpnt_indx - 1) % len(self.keypoints_spec)

    def cycle_next(self):
        self.kpnt_indx = (self.kpnt_indx + 1) % len(self.keypoints_spec)

    @property
    def kpnt_indx(self):
        """ The index of the keypoint currently being edited.

        When set, the previous and the next keypoints are updated as well as the name of the current.
        """
        return self._kpnt_indx

    @kpnt_indx.setter
    def kpnt_indx(self, new_indx):
        self._kpnt_indx = new_indx
        self.prev_kpnt = self.keypoints_spec[(self._kpnt_indx - 1) % len(self.keypoints_spec)]['name']
        self.next_kpnt = self.keypoints_spec[(self._kpnt_indx + 1) % len(self.keypoints_spec)]['name']

        self.name = self.keypoints_spec[self._kpnt_indx]['name'].title()
        self.setup_highlight(self.keypoints_spec[self._kpnt_indx]['smpl_indx'])


class EditorControls(AbstractControls):

    frame_indx = NumericProperty(0)

    def __init__(self, edit_actions, exercises, info_label, *args, **kwargs):
        self.info_label = info_label
        super().__init__(edit_actions, exercises, *args, **kwargs)

        self.user_touching_slider = False
        self.ids.prog_slider.bind(value=self.on_slider_value)

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
        """ Start the `predict` action to save the results of an exercise video as groundtruth correct. """
        self.dismiss_popup()
        if type(filename) == int:
            files = sorted(os.listdir(path))
            filename = files[filename]

        self.info_label.text = f'Predicting from the file: {filename[0]}'
        source = os.path.join(path, filename[0])
        self.actions['playback'].stop()
        self.actions['predict'].initialize(self.smpl_mode, source=source, save_exercise=True)
        self.frame_indx = 0

    def start_playback(self, exercise):
        """ Start the `playback` action to playback a saved exercise. """
        if exercise in self.exercises.keys():
            self.info_label.text = f'Exercise playback: {exercise}'
            self.ids.prog_slider.max = len(self.exercises[exercise]) - 1
            self.actions['predict'].stop()
            self.actions['playback'].initialize(self.smpl_mode, self.exercises[exercise])

    def display_kpnt_edit_form(self, kpnt_name: str, keypoints_spec):
        """ Display a popup with the keypoint edit dialog. """
        self.dismiss_kpnt_edit_form()

        self.kpnt_edit_form = KeypointEditForm(name=kpnt_name, keypoints_spec=keypoints_spec,
                                               setup_highlight=self.actions['playback'].renderer.setup_highlight,
                                               save_kpnt_options=self.save_kpnt_options,
                                               cancel=self.dismiss_kpnt_edit_form)
        self.parent.parent.parent.add_widget(self.kpnt_edit_form)

    def save_kpnt_options(self):
        self.dismiss_kpnt_edit_form()

    def dismiss_kpnt_edit_form(self):
        try:
            self.parent.parent.parent.remove_widget(self.kpnt_edit_form)
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
