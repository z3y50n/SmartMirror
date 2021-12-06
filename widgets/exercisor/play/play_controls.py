from widgets.exercisor.controls import AbstractControls
from widgets.exercisor.utils.log import logger


class PlayControls(AbstractControls):
    def __init__(self, actions, info_label, *args, **kwargs):
        super().__init__(actions, info_label, *args, **kwargs)

    def demo_render(self, rendered_obj):
        if rendered_obj == "smpl":
            self.actions["play"].stop()
            self.actions["predict"].initialize(self.smpl_mode)
        elif rendered_obj in ("monkey", "monkey_no_norms", "random"):
            self.actions["play"].demo_render(rendered_obj)

        if rendered_obj in self.ids.demo_render_spin.values:
            self.info_label.text = f"Rendering the object {rendered_obj}..."

    def start_exercise(self, exercise_name: str):
        if exercise_name in self.exercises.keys():
            super().start_exercise(exercise_name)
            self.actions["predict"].stop()
            self.actions["play"].initialize(
                self.smpl_mode, {"name": exercise_name}, self.exercises[exercise_name]
            )

    def reset_ui(self):
        # self.ids.demo_render_spin.text = 'Render'
        super().reset_ui()
