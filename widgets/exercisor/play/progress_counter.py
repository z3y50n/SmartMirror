from kivy.uix.progressbar import ProgressBar
from kivy.core.text import Label as CoreLabel
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Line
from kivy.properties import NumericProperty, OptionProperty, ColorProperty
from kivy.clock import Clock


class CircularProgressBar(ProgressBar):

    background_color = ColorProperty((0.26, 0.26, 0.26))
    progress_color = ColorProperty((0.3, 0.0, 0.3))

    def __init__(self, **kwargs):
        super(CircularProgressBar, self).__init__(**kwargs)

        # Set constant for the bar thickness
        self._thickness = 8

        self._cap_style = "round"
        self._cap_precision = 10

        # Create a direct text representation
        self._text_label = CoreLabel(text="0", font_size=25, halign="center")

    def draw(self):

        with self.canvas:

            self.canvas.clear()
            self._refresh_text()
            circle_center_x = self.pos[0] + self.size[0] / 2
            circle_center_y = self.pos[1] + self.size[1] / 2
            circle_radius = self.size[0] / 2 - self._thickness

            # Draw background circle
            Color(*self.background_color)
            Line(
                circle=(circle_center_x, circle_center_y, circle_radius),
                width=self._thickness,
            )

            # Draw the progress line
            normalised = (self.value - self.min) / (self.max - self.min)
            if normalised > 0:
                Color(*self.progress_color)
                Line(
                    circle=(
                        circle_center_x,
                        circle_center_y,
                        circle_radius,
                        0,
                        normalised * 360,
                    ),
                    width=self._thickness,
                    cap=self._cap_style,
                    cap_precision=self._cap_precision,
                )

            # Center and draw the progress text
            Color(1, 1, 1, 1)
            Rectangle(
                texture=self._text_label.texture,
                size=self._label_size,
                pos=(
                    self.size[0] / 2 - self._label_size[0] / 2 + self.pos[0],
                    self.size[1] / 2 - self._label_size[1] / 2 + self.pos[1],
                ),
            )

    def _refresh_text(self):
        # Render the label and set the size depending on the text
        self._text_label.refresh()
        self._label_size = list(self._text_label.texture.size)

    def set_value(self, value):
        # Update the progress bar value
        self.value = value

        # Update textual value and refresh the texture
        if self.mode == "timer":
            self._text_label.text = (
                f"{int(self.value / 60)}:{str(self.value % 60).zfill(2)}"
            )
        else:
            self._text_label.text = f"{int(self.value)}"
        self._refresh_text()

        # Draw all the elements
        self.draw()


class ProgressCounter(FloatLayout):
    mode = OptionProperty("repetition", options=["repetition", "timer"])

    counter = NumericProperty(-1)
    min_count = NumericProperty(1)
    max_count = NumericProperty(10)

    def __init__(self, stop_action, **kwargs):
        self._stop_action = stop_action
        super().__init__(**kwargs)

    def on_mode(self, _, new_mode):
        self.ids.prog_desc.text = new_mode.capitalize()
        if new_mode == "timer":
            self.min_count = 0
            self._timer_event = Clock.schedule_interval(self._countdown, 1)
        elif new_mode == "repetition":
            self.min_count = 1
            if hasattr(self, "_timer_event"):
                self._timer_event.cancel()

    def on_counter(self, _, new_val):
        self.ids.progress.set_value(new_val)
        if (self.mode == "repetition" and self.counter == self.max_count) or (
            self.mode == "timer" and self.counter == self.min_count
        ):
            self._stop_action()

    def on_max_count(self, _, new_max_count):
        self.ids.progress.max = new_max_count

    def _countdown(self, dt):
        self.counter -= 1
