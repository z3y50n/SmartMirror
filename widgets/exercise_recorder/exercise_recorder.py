import json
import os
import cv2
import threading
import time

from kivy.uix.widget import Widget
from kivy.base import runTouchApp
from kivy.lang import Builder

import model_cfg
from renderer import Renderer
from predictor import Predictor

CONFIG_PATH = os.path.join(os.path.dirname(
    os.path.abspath('config.json')), 'config.json')


class ExerciseRecorder(Widget):
    """
    The ExerciseRecorder widget displays the camera input and the 3D model
    prediction.
    """
    def __init__(self, **kwargs):
        super(ExerciseRecorder, self).__init__(**kwargs)

        # Import config file
        with open(CONFIG_PATH, 'r') as f:
            cfg_dict = json.load(f)

            if 'EXERCISE_RECORDER' in cfg_dict.keys():
                self.cfg = cfg_dict['EXERCISE_RECORDER']

        self.model = Predictor(model_cfg)
        self.renderer = Renderer(smpl_faces_path=model_cfg.smpl_faces_path)

    def predict(self):
        threading.Thread(target=self.predict_thread()).start()

    def predict_thread(self):
        cap = cv2.VideoCapture(0)

        winframes = 4
        winq = []
        while(True):

            # Capture frame-by-frame
            ret, frame = cap.read()

            start = time.time()
            joints, verts, cams, joints3d, theta = self.model.predict(
                frame, get_theta=True)

            # Display input image and render the 3d model
            cv2.imshow('frame', frame)

            self.renderer.set_data(verts[0])
            # Print the frames per second
            end = time.time()
            winq.append(end - start)
            if len(winq) == winframes:
                print("FPS:", winframes / sum(winq))
                winq.pop(0)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':

    Builder.load_file('exercise_recorder.kv')
    runTouchApp(ExerciseRecorder())
