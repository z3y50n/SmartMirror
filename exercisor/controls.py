
from kivy.properties import DictProperty
from kivy.uix.boxlayout import BoxLayout


class AbstractControls(BoxLayout):

    exercises = DictProperty(force_dispatch=True, rebind=True)

    def __init__(self, actions, exercises, *args, **kwargs):
        self.actions = actions
        self.exercises = exercises
        self.smpl_mode = 'smpl_mesh'
        super().__init__(*args, **kwargs)

    def on_play_pause(self, state):
        """ Control the pausing and resuming of the active actions """

        if state == 'down':
            for action in self.actions.values():
                if action.running:
                    action.resume()
                    return
            # If no actions are running then return the button to the 'normal' state
            self.ids.play_pause_btn.state = 'normal'
        elif state == 'normal':
            for action in self.actions.values():
                action.pause()

    def set_smpl_mode(self, mode, is_active):
        """ Set the smpl mode depending on which checkbutton is active. The playback remains in the paused or playing state.

        Parameters
        ----------
        mode: {'mesh', 'kpnts'}
            Specifies which mode corresponds to the checkbox that called the function
        is_active: boolean
            The state of the checkbox. When it is active, the corresponding mode is set
        """
        if is_active:
            self.smpl_mode = f'smpl_{mode}'
            for action in self.actions.values():
                if action.running:
                    was_playing = not action.paused
                    action.reset_renderers()
                    action.init_renderers(self.smpl_mode)
                    if was_playing:
                        self.ids.play_pause_btn.state = 'down'

    def reset_ui(self):
        self.ids.choose_exercise_spin.text = ''
        self.ids.play_pause_btn.state = 'normal'
