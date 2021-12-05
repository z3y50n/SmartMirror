import numpy as np
from math import atan2, asin, pi, cos, sin, degrees


def quaternion_to_euler(qua):
    L = (qua[0]**2 + qua[1]**2 + qua[2]**2 + qua[3]**2)**0.5
    w = qua[0] / L
    x = qua[1] / L
    y = qua[2] / L
    z = qua[3] / L
    Roll = atan2(2 * (w * x + y * z), 1 - 2 * (x**2 + y**2))
    if Roll < 0:
        Roll += 2 * pi

    temp = w * y - z * x
    if temp >= 0.5:
        temp = 0.5
    elif temp <= -0.5:
        temp = -0.5

    Pitch = asin(2 * temp)
    Yaw = atan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))
    if Yaw < 0:
        Yaw += 2 * pi
    return [Yaw, Pitch, Roll]


def euler_to_quaternion(ypr):
    y, p, r = ypr
    roll = r / 2
    pitch = p / 2
    yaw = y / 2

    w = cos(roll) * cos(pitch) * cos(yaw) + \
        sin(roll) * sin(pitch) * sin(yaw)
    x = sin(roll) * cos(pitch) * cos(yaw) - \
        cos(roll) * sin(pitch) * sin(yaw)
    y = cos(roll) * sin(pitch) * cos(yaw) + \
        sin(roll) * cos(pitch) * sin(yaw)
    z = cos(roll) * cos(pitch) * sin(yaw) + \
        sin(roll) * sin(pitch) * cos(yaw)
    qua = [w, x, y, z]
    return qua


def quat_mult(q1, q2):

    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    return np.array([w, x, y, z])


def euler_to_roll_pitch_yaw(lst):
    return [degrees(i) for i in lst]
