import errno
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
    """
    Creates a thread that will load the SMPL model.

    Attributes
    ----------
    smpl_model_path: str
        The path where the SMPL model is saved.
    joint_type: {'cocoplus', 'lsp'}
        The type of joints to be used. Cocoplus has 19 joints and lsp has 14 joints.
        In this custom implementation the SMPL model always returns the 24 smpl joints.
    output_fn: function
        The function to call on the outputs for each prediction.
    frame_index: int
        The current frame of the exercise playback.
    graph: tensorflow.Graph
        The computational graph to be used.
    sess: tensorflow.Session
        The session to be used.
    smpl: tf_smpl.batch_smpl.SMPL
        The SMPL model implementation in tensorflow.
    thetas: tensorflow.Tensor
        The input tensor that holds the pose and shape coefficients for the SMPL model.
    verts: tensorflow.Tensor
        The output tensor that holds the vertices of the smpl mesh.
    joints: tensorflow.Tensor
        The output tensor that holds the 24 keypoints of the smpl mesh.
    """
    def __init__(self, smpl_model_path, joint_type, output_fn, *args, **kwargs):
        self.smpl_model_path = smpl_model_path
        self.joint_type = joint_type
        self.output_fn = output_fn
        self.frame_index = 0
        super().__init__('SMPL', *args, **kwargs)

    def prepare_model(self):
        """ Create the tensorflow graph and session and build the SMPL model. """
        self.graph = tf.Graph()
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.compat.v1.Session(graph=self.graph, config=config)
        with self.graph.as_default():
            self.build_model()

    def build_model(self):
        """ Load the SMPL model, create the input and output tensors and initialise the session. """
        self.smpl = SMPL(self.smpl_model_path, self.joint_type)
        # Thetas are 10 shape coefficients of SMPL
        # and 72 pose variables holding the rotation of 24 joints in axis angle format
        self.thetas = tf.compat.v1.placeholder(tf.float32, shape=(1, 82))

        pose, shape = self.thetas[:, :72], self.thetas[:, 72:]
        self.verts, _, self.joints = self.smpl(shape, pose, get_skin=True)

        init = tf.compat.v1.global_variables_initializer()
        self.sess.run(init)

    def prepare_inputs(self):
        """ Get the current frame's thetas and add the batch dimension. """
        thetas = self.exercise[self.frame_index % len(self.exercise)]
        thetas = np.expand_dims(thetas, axis=0)
        return thetas

    def predict(self, thetas):
        """ Create the inputs and expected outputs and run the prediction. """
        feed_dict = {self.thetas: thetas}
        fetch_dict = {
            'vertices': self.verts,
            'keypoints': self.joints
        }
        outputs = self.sess.run(fetch_dict, feed_dict)
        return outputs

    def process_outputs(self, outputs):
        """ Run the specified function with the outputs of the prediction and go to the next frame. """
        self.output_fn(outputs['vertices'][0], outputs['keypoints'][0])
        self.frame_index += 1

    def cleaning_up(self):
        pass

    @property
    def exercise(self):
        """ array_like (N x 82): The 82 thetas for each of the N frames of the current exercise.

        When setting a new exercise, reset the the index of the current frame as well.
        """
        return self._exercise

    @exercise.setter
    def exercise(self, ex):
        self.frame_index = 0
        self._exercise = ex


class HMRThread(MLThread):
    """
    Creates a thread that will load the HMR model.

    Attributes
    ----------
    model_cfg: module
        The configuration options for the HMR model.
    img_size: int
        The size in pixels of both dimensions of the input image.
    output_fn: function
        The function to call on the outputs for each prediction.
    save_fn: function
        Saves the predicted outputs for a specific exercise.
    graph: tensorflow.Graph
        The computational graph to be used.
    sess: tensorflow.Session
        The session to be used.
    model: models.HMR
        The HMR model implementation in tensorflow.
    thetas: list of lists
        The 82 thetas for each frame to be saved when saving an exercise.
    source: str
        The source stream to be used in the capture. Can be either 'cam' or a video file path.
    """
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
        """ Create the tensorflow graph and session and load the model """
        self.graph = tf.Graph()
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.compat.v1.Session(graph=self.graph, config=config)
        with self.graph.as_default():
            self.model = self.load_model()

    def load_model(self):
        """ Load the HMR model """
        model = HMR(self.model_cfg, sess=self.sess)
        self.thetas = []
        return model

    def prepare_inputs(self):
        """
        Get the next frame from the capture and preprocess the frame image.

        Returns
        -------
        dict
            The retrieval bool and the current frame image.
            The retrieval bool is True if the frame retrieval was successful, False otherwise.
            The frame image is an array_like.
        """
        ret, frame = self.capture.read()
        frame, _ = process_image(frame, self.img_size)
        inputs = {'ret': ret, 'frame': frame}
        return inputs

    def predict(self, inputs):
        """
        Display the input frame image and return the predictions, if the frame retrieval was successful.

        Parameters
        ----------
        inputs : dict
            The returned dict of :method: prepare_inputs() as described above.

        Returns
        -------
        dict
            The vertices and keypoints of the smpl mesh if the frame retrieval was successful.
            Otherwise, if it was saving an exercise, returns the thetas for the whole exercise.
        """
        if inputs['ret']:
            joints, verts, cams, joints3d, theta = self.model.predict(inputs['frame'], get_theta=True)

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
        """ Call either the output_fn or the save_fn depending on the type of output """
        if 'thetas' in outputs.keys():
            filename = os.path.basename(self.source)
            filename = os.path.splitext(filename)[0]
            self.save_fn(filename, outputs['thetas'])
        elif 'verts' in outputs.keys() and 'joints3d' in outputs.keys():
            self.output_fn(new_verts=outputs['verts'], new_kpnts=outputs['joints3d'])

    def cleaning_up(self):
        """ Release the acquired capture and close the opencv windows. """
        self.capture.release()
        cv2.destroyAllWindows()

    def pause(self):
        """ Close all the opencv windows. """
        super().pause()
        cv2.destroyAllWindows()

    def save(self):
        self._saving.set()

    @property
    def capture(self):
        """ cv2.VideoCapture: The video capture stream.

        The capture source can be either 'cam' or a specified video file.

        Raises
        ------
        FileNotFoundError
            If the capture source was a video file and no file was found on that path.
        """
        return self._capture

    @capture.setter
    def capture(self, source):
        self.source = source
        if source == 'cam':
            self._capture = cv2.VideoCapture(0)
        else:
            if os.path.exists(self.source):
                self._capture = cv2.VideoCapture(self.source)
            else:
                raise FileNotFoundError(errno.ENOENT,
                                        os.strerror(errno.ENOENT), self.source)
