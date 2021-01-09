import tensorflow as tf

from models import HMR
from preprocess import process_image
import os
import threading
import time
import cv2
import numpy as np


class Predictor(object):

    def __init__(self, model_cfg):
        # Setup the session and load the hmr model
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        sess = tf.compat.v1.Session(config=config)

        self.img_size = model_cfg.img_size
        self.model = HMR(model_cfg, sess=sess)

    def predict(self, frame):
        input_img, proc_param = process_image(frame, self.img_size)
        # Theta is the 85D vector holding [camera, pose, shape]
        # where camera is 3D [s, tx, ty]
        # pose is 72D vector holding the rotation of 24 joints of SMPL in axis angle format
        # shape is 10D shape coefficients of SMPL

        return self.model.predict(input_img, get_theta=True)


class PredictThread(threading.Thread):

    def __init__(self, model_cfg, render_fn, *args, **kwargs):
        self.model_cfg = model_cfg
        self.render_fn = render_fn
        super(PredictThread, self).__init__(*args, **kwargs)
        self._running = threading.Event()
        self._running.set()
        self._resumed = threading.Event()
        self.pause()
        self._saving = threading.Event()
        self._saving.clear()

        self.set_capture('cam')

    def pause(self):
        cv2.destroyAllWindows()
        self._resumed.clear()  # Set to False to block the thread

    def resume(self):
        self._resumed.set()  # Set to True, let the thread stop blocking

    def stop(self):
        self._resumed.set()  # Resume the thread from the suspended state, if it is already suspended
        self._running.clear()  # Set to False

    def save(self):
        self._saving.set()

    def set_capture(self, source):
        self.source = source
        if source == 'cam':
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture(source)

    def run(self):
        model = Predictor(self.model_cfg)

        winframes = 4
        winq = []
        thetas = []
        print('Model finished loading')
        while(self._running.is_set()):
            self._resumed.wait()
            # Capture frame-by-frame
            ret, frame = self.cap.read()

            if ret:
                start = time.time()
                joints, verts, cams, joints3d, theta = model.predict(frame)

                if self._saving.is_set():
                    thetas.append(theta[0, 3:])

                # Display input image and render the 3d model
                cv2.imshow('frame', frame)

                self.render_fn(new_verts=verts[0], new_kpnts=joints3d[0])
                # Print the frames per second
                end = time.time()
                winq.append(end - start)
                if len(winq) == winframes:
                    print("FPS:", winframes / sum(winq))
                    winq.pop(0)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                if self._saving.is_set():
                    filename = os.path.basename(self.source)
                    filename = os.path.splitext(filename)[0]
                    thetas = np.array(thetas)
                    with open(f'./widgets/exercise_recorder/exercise_data/{filename}.npy', 'w+b') as f:
                        np.save(f, thetas)

                    self._saving.clear()
                    thetas = []
                self.pause()

        # When everything done, release the capture
        self.cap.release()
        cv2.destroyAllWindows()
