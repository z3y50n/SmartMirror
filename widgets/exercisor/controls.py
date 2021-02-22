
from kivy.properties import DictProperty
from kivy.uix.boxlayout import BoxLayout


class AbstractControls(BoxLayout):

    exercises = DictProperty({}, force_dispatch=True, rebind=True)

    def __init__(self, actions, exercises, *args, **kwargs):
        self.actions = actions
        self.exercises = exercises
        self.smpl_mode = 'smpl_mesh'
        super().__init__(*args, **kwargs)

    def on_play_pause(self, state):
        """ Controls the pausing and resuming of the active actions """

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
        if is_active:
            self.smpl_mode = f'smpl_{mode}'
            for action in self.actions.values():
                if action.running:
                    was_playing = not action.paused
                    action.reset_renderers()
                    action.init_renderers(self.smpl_mode)
                    if was_playing:
                        self.ids.play_pause_btn.state = 'down'

    def reset_buttons(self):
        self.ids.choose_exercise_spin.text = ''
        self.ids.play_pause_btn.state = 'normal'