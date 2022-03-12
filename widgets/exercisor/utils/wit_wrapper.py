class WitWrapper:
    def __init__(self, exercisor):
        self.exercisor = exercisor

    def export_functions(self):
        funcs = {
            "open": self.change_control,
            "play": self.playback,
            "pause": self.play_pause_playback,
            "control_playback": self.control_playback,
            "switch_human_form": self.switch_human_form,
        }

        return funcs

    def change_control(self):
        state = self.exercisor.ids.ctrl_btn.state
        self.exercisor.change_control("normal" if state == "down" else "down")

    def playback(self, exercise):
        self.exercisor.controls.start_exercise(exercise)

    def control_playback(self, direction, duration=5):
        if self.exercisor.actions["playback"].running:
            if direction == "back":
                duration = -duration
            self.exercisor.actions["playback"].seek(duration, fmt="duration")

    def switch_human_form(self, mode):
        if type(self.exercisor.controls) == self.exercisor.EditorControls:
            self.exercisor.controls.set_smpl_mode(mode, True)

    def play_pause_playback(self):
        state = self.exercisor.controls.ids.play_pause_btn.state
        self.exercisor.controls.on_play_pause("normal" if state == "down" else "down")
