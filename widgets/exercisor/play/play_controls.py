from controls import AbstractControls
from log import logger


class PlayControls(AbstractControls):

    def __init__(self, actions, exercises, info_label, *args, **kwargs):
        self.info_label = info_label
        super().__init__(actions, exercises, *args, **kwargs)

    def demo_render(self, rendered_obj):
        if rendered_obj == 'smpl':
            self.actions['play'].stop()
            self.actions['predict'].initialize(self.smpl_mode)
            self.actions['predict'].resume()
        elif rendered_obj in ('monkey', 'monkey_no_norms', 'random'):
            self.actions['play'].demo_render(rendered_obj)

        if rendered_obj in self.ids.demo_render_spin.values:
            self.info_label.text = f'Rendering the object {rendered_obj}...'

    def start_playing(self, exercise):
        if exercise in self.exercises.keys():
            logger.info(f'Playing the exercise `{exercise}`...')
            self.info_label.text = f'Playing the exercise {exercise}...'
            self.actions['predict'].stop()
            self.actions['play'].initialize(self.smpl_mode, self.exercises[exercise])
            self.actions['play'].resume()

    def reset_buttons(self):
        self.ids.demo_render_spin.text = 'Render'
        super().reset_buttons()
