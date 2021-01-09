import tensorflow as tf

from ml_thread import MLThread
from models import HMR
from preprocess import process_image
from tf_smpl.batch_smpl import SMPL


class SMPLModel(MLThread):

    def __init__(self, smpl_model_path, joint_type, *args, **kwargs):
        self.smpl_model_path = smpl_model_path
        self.joint_type = joint_type

    def load_model(self):
        self.smpl = SMPL(self.smpl_model_path, self.joint_type)
        # Thetas are 10 shape and 72 pose variables
        self.thetas = tf.compat.v1.placeholder(tf.float32, shape=(1, 82))
        self.build_test_model()
        init = tf.compat.v1.global_variables_initializer()

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


class HMRModel(MLThread):

    def __init__(self, model_cfg, *args, **kwargs):
        # Setup the session and load the hmr model
        self.model_cfg = model_cfg
        self.img_size = model_cfg.img_size

    def load_model(self):
        self.model = HMR(self.model_cfg, sess=self.sess)

    def predict(self, frame):
        input_img, proc_param = process_image(frame, self.img_size)
        # Theta is the 85D vector holding [camera, pose, shape]
        # where camera is 3D [s, tx, ty]
        # pose is 72D vector holding the rotation of 24 joints of SMPL in axis angle format
        # shape is 10D shape coefficients of SMPL

        return self.model.predict(input_img, get_theta=True)
