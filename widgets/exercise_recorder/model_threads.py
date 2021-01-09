import os
import numpy as np
import cv2
import threading
import tensorflow as tf

from ml_thread import MLThread
from models import HMR
from preprocess import process_image
from tf_smpl.batch_smpl import SMPL


class SMPLThread(MLThread):

    def __init__(self, smpl_model_path, joint_type, output_fn, *args, **kwargs):
        self.smpl_model_path = smpl_model_path
        self.joint_type = joint_type
        self.output_fn = output_fn
        self.frame_count = 0
        super().__init__('SMPL', *args, **kwargs)

    def prepare_model(self):
        self.graph = tf.Graph()
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.compat.v1.Session(graph=self.graph, config=config)
        with self.graph.as_default():
            self.build_model()

    def build_model(self):
        self.smpl = SMPL(self.smpl_model_path, self.joint_type)
        # Thetas are 10 shape coefficients of SMPL
        # and 72 pose variables holding the rotation of 24 joints of SMPL in axis angle format
        self.thetas = tf.compat.v1.placeholder(tf.float32, shape=(1, 82))

        pose, shape = self.thetas[:, :72], self.thetas[:, 72:]
        self.verts, _, self.joints = self.smpl(shape, pose, get_skin=True)

        init = tf.compat.v1.global_variables_initializer()
        self.sess.run(init)

    def prepare_inputs(self):
        thetas = self.exercise[self.frame_count % len(self.exercise)]
        thetas = np.expand_dims(thetas, axis=0)
        return thetas

    def predict(self, thetas):
        feed_dict = {self.thetas: thetas}
        fetch_dict = {
            'vertices': self.verts,
            'keypoints': self.joints
        }
        outputs = self.sess.run(fetch_dict, feed_dict)
        return outputs

    def process_outputs(self, outputs):
        self.output_fn(outputs['vertices'][0], outputs['keypoints'][0])
        self.frame_count += 1

    def cleaning_up(self):
        pass

    @property
    def exercise(self):
        return self._exercise

    @exercise.setter
    def exercise(self, ex):
        self.frame_count = 0
        self._exercise = ex


class HMRThread(MLThread):

    def __init__(self, model_cfg, output_fn, save_fn, *args, **kwargs):
        # Setup the session and load the hmr model
        self.model_cfg = model_cfg
        self.img_size = model_cfg.img_size
        self.output_fn = output_fn
        self.save_fn = save_fn

        self.capture = 'cam'

        self._saving = threading.Event()
        super().__init__('HMR', *args, **kwargs)

    def prepare_model(self):
        self.graph = tf.Graph()
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.compat.v1.Session(graph=self.graph, config=config)
        with self.graph.as_default():
            self.model = self.load_model()

    def load_model(self):
        model = HMR(self.model_cfg, sess=self.sess)
        self.thetas = []
        return model

    def prepare_inputs(self):
        ret, frame = self.capture.read()
        inputs = {'ret': ret, 'frame': frame}
        return inputs

    def predict(self, inputs):
        if inputs['ret']:
            proc_img, _ = process_image(inputs['frame'], self.img_size)
            joints, verts, cams, joints3d, theta = self.model.predict(proc_img, get_theta=True)

            if self._saving.is_set():
                self.thetas.append(theta[0, 3:])

            # Display input image
            cv2.imshow('frame', inputs['frame'])
            cv2.waitKey(1)
            outputs = {'verts': verts[0], 'joints3d': joints3d[0]}
            return outputs
        else:
            if self._saving.is_set():
                thetas = np.array(self.thetas)
                self._saving.clear()
                self.thetas = []
                self.pause()
                return {'thetas': thetas}

    def process_outputs(self, outputs):
        if 'thetas' in outputs.keys():
            filename = os.path.basename(self.source)
            filename = os.path.splitext(filename)[0]
            self.save_fn(filename, outputs['thetas'])
        else:
            self.output_fn(new_verts=outputs['verts'], new_kpnts=outputs['joints3d'])

    def cleaning_up(self):
        self.capture.release()
        cv2.destroyAllWindows()

    def pause(self):
        super().pause()
        cv2.destroyAllWindows()

    def save(self):
        self._saving.set()

    @property
    def capture(self):
        return self._capture

    @capture.setter
    def capture(self, source):
        self.source = source
        if source == 'cam':
            self._capture = cv2.VideoCapture(0)
        else:
            self._capture = cv2.VideoCapture(source)
