import tensorflow as tf
import numpy as np
import cv2

from tf_smpl import projection as proj_util
from tf_smpl.batch_smpl import SMPL
from models import get_encoder_fn_separate


class HMR(object):
    def __init__(self, config, sess=None):
        """
        Args:
          config
        """
        self.config = config
        self.load_path = config.pretrained_path

        # Config + path
        if not config.pretrained_path:
            raise Exception(
                "You need to specify `load_path` to load a pretrained model"
            )

        # Data
        self.batch_size = config.batch_size
        self.img_size = config.img_size

        self.data_format = config.data_format
        self.smpl_model_path = config.smpl_model_path

        input_size = (self.batch_size, self.img_size, self.img_size, 3)
        self.images_pl = tf.placeholder(tf.float32, shape=input_size)

        # Model Settings
        self.num_stage = config.num_stage
        self.model_type = config.model_type
        self.joint_type = config.joint_type
        # Camera
        self.num_cam = 3
        self.proj_fn = proj_util.batch_orth_proj_idrot

        self.num_theta = 72
        # Theta size: camera (3) + pose (24*3) + shape (10)
        self.total_params = self.num_cam + self.num_theta + 10

        self.smpl = SMPL(self.smpl_model_path, joint_type=self.joint_type)

        self.build_test_model_ief()

        if sess is None:
            self.sess = tf.Session()
        else:
            self.sess = sess

        # Load data.
        self.saver = tf.train.Saver()
        self.prepare()

    def build_test_model_ief(self):
        # Load mean value
        self.mean_var = tf.Variable(tf.zeros((1, self.total_params)), name="mean_param", dtype=tf.float32)

        img_enc_fn, threed_enc_fn = get_encoder_fn_separate(self.model_type)
        # Extract image features.
        self.img_feat, self.E_var = img_enc_fn(self.images_pl,
                                               is_training=False,
                                               reuse=False)

        # Start loop
        self.all_verts = []
        self.all_kps = []
        self.all_cams = []
        self.all_Js = []
        self.final_thetas = []
        theta_prev = tf.tile(self.mean_var, [self.batch_size, 1])
        for i in np.arange(self.num_stage):
            print('Iteration %d' % i)
            # ---- Compute outputs
            state = tf.concat([self.img_feat, theta_prev], 1)

            if i == 0:
                delta_theta, _ = threed_enc_fn(
                    state,
                    num_output=self.total_params,
                    is_training=False,
                    reuse=False)
            else:
                delta_theta, _ = threed_enc_fn(
                    state,
                    num_output=self.total_params,
                    is_training=False,
                    reuse=True)

            # Compute new theta
            theta_here = theta_prev + delta_theta
            # cam = N x 3, pose N x self.num_theta, shape: N x 10
            cams = theta_here[:, :self.num_cam]
            poses = theta_here[:, self.num_cam:(self.num_cam + self.num_theta)]
            shapes = theta_here[:, (self.num_cam + self.num_theta):]

            verts, Js, _ = self.smpl(shapes, poses, get_skin=True)

            # Project to 2D!
            pred_kp = self.proj_fn(Js, cams, name='proj_2d_stage%d' % i)
            self.all_verts.append(verts)
            self.all_kps.append(pred_kp)
            self.all_cams.append(cams)
            self.all_Js.append(Js)
            # save each theta.
            self.final_thetas.append(theta_here)
            # Finally)update to end iteration.
            theta_prev = theta_here

    def prepare(self):
        print('Restoring checkpoint %s..' % self.load_path)
        self.saver.restore(self.sess, self.load_path)
        self.mean_value = self.sess.run(self.mean_var)

    def predict(self, images, get_theta=False):
        """
        images: num_batch, img_size, img_size, 3
        Preprocessed to range [-1, 1]
        """
        results = self.predict_dict(images)
        if get_theta:
            return results['joints'], results['verts'], results['cams'], \
                results['joints3d'], results['theta']
        else:
            return results['joints'], results['verts'], results['cams'], \
                results['joints3d']

    def predict_dict(self, images):
        """
        images: num_batch, img_size, img_size, 3
        Preprocessed to range [-1, 1]
        Runs the model with images.
        """
        feed_dict = {
            self.images_pl: images,
            # self.theta0_pl: self.mean_var,
        }
        fetch_dict = {
            'joints': self.all_kps[-1],
            'verts': self.all_verts[-1],
            'cams': self.all_cams[-1],
            'joints3d': self.all_Js[-1],
            'theta': self.final_thetas[-1],
        }

        results = self.sess.run(fetch_dict, feed_dict)

        # Return joints in original image space.
        joints = results['joints']
        results['joints'] = ((joints + 1) * 0.5) * self.img_size

        return results


class Predictor(object):

    def __init__(self, model_cfg):
        # Setup the session and load the hmr model
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        sess = tf.Session(config=config)

        self.img_size = model_cfg.img_size
        self.model = HMR(model_cfg, sess=sess)

    def predict(self, frame, get_theta=True):
        input_img, proc_param = self.preprocess_image(frame)
        # Theta is the 85D vector holding [camera, pose, shape]
        # where camera is 3D [s, tx, ty]
        # pose is 72D vector holding the rotation of 24 joints of SMPL in axis angle format
        # shape is 10D shape coefficients of SMPL

        return self.model.predict(input_img, get_theta=True)

    def preprocess_image(self, img):

        if np.max(img.shape[:2]) != self.img_size:
            # print('Resizing so the max image size is %d..' % img_size)
            scale = (float(self.img_size) / np.max(img.shape[:2]))
        else:
            scale = 1.
        center = np.round(np.array(img.shape[:2]) / 2).astype(int)
        # image center in (x,y)
        center = center[::-1]

        crop, proc_param = self.scale_and_crop(img, scale, center, self.img_size)

        # Normalize image to [-1, 1]
        crop = 2 * ((crop / 255.) - 0.5)

        # Add batch dimension: 1 x D x D x 3
        return np.expand_dims(crop, 0), proc_param

    def scale_and_crop(self, image, scale, center, img_size):
        image_scaled, scale_factors = self.resize_img(image, scale)
        # Swap so it's [x, y]
        scale_factors = [scale_factors[1], scale_factors[0]]
        center_scaled = np.round(center * scale_factors).astype(np.int)

        margin = int(img_size / 2)
        image_pad = np.pad(
            image_scaled, ((margin, ), (margin, ), (0, )), mode='edge')
        center_pad = center_scaled + margin
        # figure out starting point
        start_pt = center_pad - margin
        end_pt = center_pad + margin
        # crop:
        crop = image_pad[start_pt[1]:end_pt[1], start_pt[0]:end_pt[0], :]
        proc_param = {
            'scale': scale,
            'start_pt': start_pt,
            'end_pt': end_pt,
            'img_size': img_size
        }

        return crop, proc_param

    def resize_img(self, img, scale_factor):
        new_size = (np.floor(np.array(img.shape[0:2]) * scale_factor)).astype(int)
        new_img = cv2.resize(img, (new_size[1], new_size[0]))
        # This is scale factor of [height, width] i.e. [y, x]
        actual_factor = [
            new_size[0] / float(img.shape[0]), new_size[1] / float(img.shape[1])
        ]
        return new_img, actual_factor
