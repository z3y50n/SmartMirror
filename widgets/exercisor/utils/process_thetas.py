from typing import Dict, List
import math
import numpy as np


def smooth_thetas(thetas: np.ndarray, window: int):
    """Smooth the frames of the saved exercised via moving average on the thetas

    Parameters
    ----------
    thetas : `numpy.ndarray`, (N x 82)
        The 82 SMPL parameters for each of the N frames
    window : `int`
        The sample window of the moving average
    """
    left = int(window / 2)
    right = int(window / 2) if window % 2 == 0 else int(window / 2) + 1
    for nf in range(0, thetas.shape[0]):
        for kid in range(0, 72, 3):
            lb = nf - left if nf - left >= 0 else 0
            rb = nf + right if nf + right < thetas.shape[0] else thetas.shape[0] - 1
            thetas[nf, kid : kid + 3] = thetas[lb:rb, kid : kid + 3].mean(axis=0)

    return thetas


def apply_fixed_rule(thetas: np.ndarray, indx: int, angles: float):
    thetas = thetas.copy()

    rads = (math.pi * angles) / 180
    prev_values = []
    for frame_indx in range(len(thetas)):
        prev_values.append(thetas[frame_indx, indx])
        thetas[frame_indx, indx] = rads

    return thetas, prev_values


def apply_range_rule(thetas: np.ndarray, indx: int, ranges: List[float]):
    thetas = thetas.copy()

    rads = [(math.pi * deg) / 180 for deg in ranges]
    prev_values = []
    for frame_indx in range(len(thetas)):
        prev_values.append(thetas[frame_indx, indx])
        if thetas[frame_indx, indx] < rads[0]:
            thetas[frame_indx, indx] = rads[0]
        elif thetas[frame_indx, indx] > rads[1]:
            thetas[frame_indx, indx] = rads[1]

    return thetas, prev_values


def apply_rules(thetas: np.ndarray, rules: Dict):
    switcher = {"fixed": apply_fixed_rule, "range": apply_range_rule}

    for (smpl_kpnt_indx, axis), (type, angles) in rules.items():
        print(f"{smpl_kpnt_indx}, {axis} | {type}, {angles}")
