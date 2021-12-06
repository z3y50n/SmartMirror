from typing import Callable, Union
import math
import re

import numpy as np

from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    StringProperty,
    ListProperty,
)

from ..utils.observable import Observable
from ..utils.log import logger


class RotTextInput(TextInput):
    pat = re.compile("[^0-9:.-]")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.focus = True

    def insert_text(self, substring, from_undo=False):
        if self.pat.match(substring):
            return
        return super().insert_text(substring, from_undo=from_undo)

    def on_focus(self, instance, focus):
        """ "Validate the text, when the text input loses focus."""
        if not focus:
            self.parent.validate_rule(self.text)


class RotInputForm(BoxLayout):

    text = StringProperty("", rebind=True)
    hint_text = StringProperty("Angle")

    def __init__(
        self,
        type: str = "fixed",
        group: int = 0,
        apply_rule: Callable = None,
        cancel: Callable = None,
        **kwargs,
    ):
        self.type = type
        self.group = group
        self._apply_rule = apply_rule
        self.cancel = cancel
        super().__init__(**kwargs)

    def validate_rule(self, rule_str):
        if self.type == "fixed":
            try:
                rot_angle = float(rule_str)
            except ValueError:
                print("The rotation angle is not valid.")
                return False
        else:
            angles = rule_str.split(":")
            if len(angles) != 2:
                print("2 angle numbers separated by `:` are expected for the range.")
                return False
            rot_angle = []
            try:
                for angle in angles:
                    rot_angle.append(float(angle))
            except ValueError:
                print("One rotation angle is not valid.")
                return False

            if rot_angle[0] > rot_angle[1]:
                print("The first angle must be lower than the second")
                return False

        self._apply_rule(self.type, int(self.group), rot_angle)
        return True


class KeypointEditForm(FloatLayout):
    """A form to edit the movement of a selected keypoint from the rendered mesh.

    Attributes
    ----------
    keypoints_spec : `list [dict]`
        A list of dictionaries containing the SMPL keypoints' specifications.
    curr_kpnt : `kivy.properties.StringProperty`
        The name of the selected keypoint.
    setup_highlight : `callable`
        A function that highlights the currently selected keypoint.
    save_kpnt_options : `kivy.properties.ObjectProperty`
        A function to save the editted options of the keypoint.
    cancel_form : `kivy.properties.ObjectProperty`
        A function to close the form.
    prev_kpnt : `kivy.properties.StringProperty`
        The name of the previous keypoint.
    next_kpnt : `kivy.properties.StringProperty`
        The name of the next keypoint.
    """

    curr_kpnt = StringProperty("", rebind=True)
    frame_indx = NumericProperty(0)
    save_kpnt_options = ObjectProperty(None)
    cancel_form = ObjectProperty(None)
    prev_kpnt = StringProperty("", rebind=True)
    next_kpnt = StringProperty("", rebind=True)

    rotation = ListProperty([], rebind=True)

    def __init__(
        self,
        keypoints_spec,
        curr_kpnt,
        setup_highlight,
        exercise_controller,
        *args,
        **kwargs,
    ):
        self.keypoints_spec = keypoints_spec
        self._setup_highlight = setup_highlight
        self._exercise_controller = exercise_controller
        self._current_thetas = exercise_controller.exercises[
            exercise_controller.current_exercise
        ]

        self.set_curr_keypoint(curr_kpnt)
        super().__init__(*args, **kwargs)

    def set_curr_keypoint(self, kpnt_name):
        self.kpnt_indx = next(
            i for i, kpnt in enumerate(self.keypoints_spec) if kpnt["name"] == kpnt_name
        )

    def cycle_prev(self):
        self.kpnt_indx = (self.kpnt_indx - 1) % len(self.keypoints_spec)

    def cycle_next(self):
        self.kpnt_indx = (self.kpnt_indx + 1) % len(self.keypoints_spec)

    @property
    def kpnt_indx(self):
        """The index of the keypoint currently being edited.

        When set, the current, the previous and the next keypoints' names are updated.
        """
        return self._kpnt_indx

    @kpnt_indx.setter
    def kpnt_indx(self, new_indx):
        self._kpnt_indx = new_indx
        self._smpl_kpnt_indx = self.keypoints_spec[self._kpnt_indx]["smpl_indx"]
        self.prev_kpnt = self.keypoints_spec[
            (self._kpnt_indx - 1) % len(self.keypoints_spec)
        ]["name"]
        self.next_kpnt = self.keypoints_spec[
            (self._kpnt_indx + 1) % len(self.keypoints_spec)
        ]["name"]

        self.curr_kpnt = self.keypoints_spec[self._kpnt_indx]["name"].title()

        self._setup_highlight(self._smpl_kpnt_indx)
        self.on_frame_indx(
            self, self.frame_indx
        )  # trigger update of the keypoint's rotation values

        # self._update_rules_form()

    def _update_rules_form(self):
        rules = self._exercise_controller.rules[
            self._exercise_controller.current_exercise
        ]
        for theta_indx, (type, angles) in rules.items():
            smpl_indx, axis = int(theta_indx / 3), theta_indx % 3

            if self._smpl_kpnt_indx == smpl_indx:
                print(axis, type, angles)
                layout = self.ids.get(f"{type}_layout")
                children = layout.children[:]
                for child in children:
                    if axis == child.group:
                        # Replace the checkbox with the text input at that position
                        text = str(angles) if type == "fixed" else ":".join(angles)
                        text_input = self._create_rot_input_form(type, axis, text)
                        children.insert(children.index(child), text_input)
                        children.remove(child)

    def on_frame_indx(self, instance, frame_indx):
        rot_thetas = self._current_thetas[self.frame_indx]

        self.rotation = [
            round(rot * 180 / math.pi, 2)
            for rot in rot_thetas[
                3 * self._smpl_kpnt_indx : 3 * self._smpl_kpnt_indx + 3
            ]
        ]

    def on_checkbox_active(self, checkbox):
        if checkbox.active:
            layout = checkbox.parent
            children = layout.children[:]

            text_input = self._create_rot_input_form(checkbox.type, int(checkbox.group))

            # Replace the checkbox with the text input at that position
            children.insert(children.index(checkbox), text_input)
            children.remove(checkbox)
        else:
            layout = self.ids.get(f"{checkbox.type}_layout")
            children = layout.children[:]
            for child in children:
                if type(child) == RotInputForm and child.group == checkbox.group:
                    # Create the checkbox and bind the `on_active` event
                    new_checkbox = Factory.BackgroundCheckBox(
                        group=checkbox.group, type=checkbox.type
                    )
                    new_checkbox.bind(
                        active=lambda chk, state: self.on_checkbox_active(chk)
                    )
                    # Replace the text input with the checkbox at that position
                    children.insert(children.index(child), new_checkbox)
                    children.remove(child)
                    self._delete_rule(int(checkbox.group))
        layout.clear_widgets()
        for child in children[::-1]:
            layout.add_widget(child)

    def _apply_rule(self, type: str, axis: int, angles: Union[float, list]):
        theta_indx = self._get_theta_indx(axis)
        self._exercise_controller.add_rule(theta_indx, type, angles)

    def _delete_rule(self, axis):
        theta_indx = self._get_theta_indx(axis)
        self._exercise_controller.delete_rule(theta_indx)

    def _create_rot_input_form(self, type: str, axis: int, text: str = None):
        if text is None:
            text = str(self.rotation[axis]) if type == "fixed" else "-90:90"

        hint_text = "degrees" if type == "fixed" else "deg1:deg2"
        text_input = RotInputForm(
            type=type,
            group=str(axis),
            text=text,
            hint_text=hint_text,
            apply_rule=self._apply_rule,
            cancel=self.on_checkbox_active,
        )

        return text_input

    def _get_theta_indx(self, axis):
        return 3 * self._smpl_kpnt_indx + axis
