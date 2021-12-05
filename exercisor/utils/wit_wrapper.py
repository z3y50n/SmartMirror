

class WitWrapper:

    def __init__(self, exercisor):
        self.exercisor = exercisor

    def export_functions(self):
        funcs = {
            'go to': self.exercisor.change_control,
            'play': self.playback,
            'control_playback': self.control_playback,
            'switch_human_form': self.switch_human_form,
            'play_pause_playback': self.play_pause_playback,
        }

        return funcs

    def playback(self, exercise):
        if type(self.exercisor.controls) == self.exercisor.EditorControls:
            self.exercisor.controls.start_exercise(exercise)
        elif type(self.exercisor.controls) == self.exercisor.PlayControls:
            self.exercisor.controls.start_exercise(exercise)

    def control_playback(self, duration=5):
        if self.exercisor.actions['playback'].running:
            self.exercisor.actions['playback'].seek(duration, fmt='duration')

    def switch_human_form(self, mode):
        if type(self.exercisor.controls) == self.exercisor.EditorControls:
            self.exercisor.controls.set_smpl_mode(mode, True)

    def play_pause_playback(self, state):
        if type(self.exercisor.controls) == self.exercisor.EditorControls:
            self.exercisor.controls.on_play_pause(state)
