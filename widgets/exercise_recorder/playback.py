import threading
import time
import numpy as np

import tensorflow as tf
from tf_smpl.batch_smpl import SMPL


class SMPLModel(object):

    def __init__(self, smpl_model_path, joint_type, *args, **kwargs):
        self.smpl_model_path = smpl_model_path
        self.joint_type = joint_type

        self.graph = tf.Graph()
        with self.graph.as_default():
            self.smpl = SMPL(self.smpl_model_path, self.joint_type)
            # Thetas are 10 shape and 72 pose variables
            self.thetas = tf.compat.v1.placeholder(tf.float32, shape=(1, 82))
            self.build_test_model()
            init = tf.compat.v1.global_variables_initializer()

        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.compat.v1.Session(graph=self.graph, config=config)

        self.sess.run(init)

    def build_test_model(self):
        pose, shape = self.thetas[:, :72], self.thetas[:, 72:]
        self.verts, _, self.joints = self.smpl(shape, pose, get_skin=True)

    def predict(self, thetas):
        feed_dict = {
            self.thetas: thetas
        }
        fetch_dict = {
            'vertices': self.verts,
            'keypoints': self.joints
        }
        results = self.sess.run(fetch_dict, feed_dict)
        return results['vertices'], results['keypoints']


class PlaybackThread(threading.Thread):

    def __init__(self, smpl_model_path, joint_type, render_fn, *args, **kwargs):
        self.render_fn = render_fn
        super(PlaybackThread, self).__init__(*args, **kwargs)
        self._resumed = threading.Event()
        self._resumed.clear()
        self._running = threading.Event()
        self._running.set()

        self.model = SMPLModel(smpl_model_path, joint_type)

        self.frame_count = 0

    def pause(self):
        self._resumed.clear()

    def resume(self):
        self._resumed.set()

    def stop(self):
        self._running.clear()

    def set_exercise(self, exercise):
        self.frame_count = 0
        self.exercise = exercise

    def run(self):
        while(self._running.is_set()):
            self._resumed.wait()
            start = time.time()
            thetas = self.exercise[self.frame_count % len(self.exercise)]
            thetas = np.expand_dims(thetas, axis=0)
            verts, joints = self.model.predict(thetas)
            self.render_fn(verts[0], joints[0])
            self.frame_count += 1
            time.sleep(max(1./25 - (time.time() - start), 0))
