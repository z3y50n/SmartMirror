from typing import Union
import os

import numpy as np

from .utils.observable import Observable
from .utils.log import logger
from .utils.process_thetas import (
    smooth_thetas,
    apply_fixed_rule,
    apply_range_rule,
    apply_rules,
)


class RulesDict(Observable, dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unsaved_rules = []

    def pop(self, key, default=None):
        self.unsaved_rules.remove(key)
        super().pop(key, default)

    def __setitem__(self, key, value):
        self.unsaved_rules.append(key)
        super().__setitem__(key, value)

    def __repr__(self):
        return f"{type(self).__name__}({super().__repr__()})"


class ExerciseController(Observable):
    """Controls the exercises of the application.

    Attributes
    ----------
    raw_exercises : `dict[str, numpy.ndarray]`
        The exercises' names and raw thetas for each frame.
    rules : `dict`
        The rules applied to each exercise.
    edited_exercises : `dict[str, numpy.ndarray]`
        The exercises after the smoothing and the application of the rules.
    """

    def __init__(self, exercises_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_exercises = self._load_exercises(exercises_path)
        self.exercises = self._smooth_exercises(self.raw_exercises)
        self.rules = {}
        self.undo_edit = {}
        self._init_rules(exercises_path)

        self.current_exercise = None

    def _load_exercises(self, folder: str):
        """Load the exercises from the specified folder"""
        if not os.path.isdir(folder):
            logger.warning(f"The path `{folder}` does not exist or it is not a folder.")
            return
        files = os.listdir(folder)
        exercises = {
            os.path.splitext(file)[0]: np.load(os.path.join(folder, file))
            for file in files
        }
        return exercises

    def _smooth_exercises(self, raw_exercises) -> dict:
        """Apply smoothing and the rules for each exercise"""
        exercises = {}
        for name, exercise in raw_exercises.items():
            exercises[name] = smooth_thetas(exercise, 10)

        return exercises

    def _init_rules(self, folder: str):
        for exercise_name in self.raw_exercises.keys():
            self.rules[exercise_name] = RulesDict({})
            self.rules[exercise_name].attach(self)
            self.undo_edit[exercise_name] = {}

        # self.rules["w_y_stretch"][38] = ("fixed", 20)

    def _apply_rule(self, theta_indx, rule_type, angles):
        if rule_type == "fixed":
            apply_rule_fn = apply_fixed_rule
        elif rule_type == "range":
            apply_rule_fn = apply_range_rule

        new_exercise_thetas, previous_thetas = apply_rule_fn(
            self.exercises[self.current_exercise], theta_indx, angles
        )
        self.exercises[self.current_exercise] = new_exercise_thetas
        self.undo_edit[self.current_exercise][theta_indx] = previous_thetas

    def _undo_rule(self, theta_indx):
        previous_thetas = self.undo_edit[self.current_exercise].pop(theta_indx)
        for frame_indx in range(len(self.exercises[self.current_exercise])):
            self.exercises[self.current_exercise][
                frame_indx, theta_indx
            ] = previous_thetas[frame_indx]

    def add_rule(self, theta_indx: int, type: str, angles: Union[float, list]):
        self.rules[self.current_exercise][theta_indx] = (type, angles)
        self._apply_rule(theta_indx, type, angles)
        self.notify()

    def delete_rule(self, theta_indx: int):
        """Delete a rule from the dictionary of rules."""
        self.rules[self.current_exercise].pop(theta_indx, None)
        self._undo_rule(theta_indx)
        self.notify()

    @property
    def exercises(self):
        """The dictionary {'name': thetas} that holds for each exercise its name and its saved thetas.

        When set, notify all the observers that the exercises have been changed.
        """
        return self._exercises

    @exercises.setter
    def exercises(self, new_exercises):
        self._exercises = new_exercises
        self.notify()
