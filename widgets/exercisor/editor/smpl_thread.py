import numpy as np
import tensorflow as tf

from ml_thread import MLThread
from tf_smpl.batch_smpl import SMPL
from log import logger


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

    def __init__(self, smpl_model_path, joint_type, *args, **kwargs):
        self.smpl_model_path = smpl_model_path
        self.joint_type = joint_type
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
        if not hasattr(self, 'exercise'):
            return
        thetas = self.exercise[self.frame_index]
        thetas = np.expand_dims(thetas, axis=0)
        return thetas

    def predict(self, thetas):
        """ Create the inputs and expected outputs and run the prediction. """
        if thetas is None:
            return

        feed_dict = {self.thetas: thetas}
        fetch_dict = {
            'vertices': self.verts,
            'keypoints': self.joints
        }
        outputs = self.sess.run(fetch_dict, feed_dict)
        return outputs

    def process_outputs(self, outputs):
        if not outputs:
            return
        """ Run the specified function with the outputs of the prediction and go to the next frame. """
        frame = {'index': self.frame_index, 'timestamp': self.start_time}
        self.output_fn(outputs['vertices'][0], outputs['keypoints'][0], frame)
        self.frame_index = (self.frame_index + 1) % len(self.exercise)

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
        self._exercise = ex
        self.frame_index = 0

    @property
    def frame_index(self):
        return self._frame_index

    @frame_index.setter
    def frame_index(self, new_frame_indx):
        try:
            if new_frame_indx < 0:
                self._frame_index = 0
            elif new_frame_indx >= len(self.exercise):
                self._frame_index = len(self.exercise) - 1
            else:
                self._frame_index = int(new_frame_indx)
        except TypeError as err:
            logger.debug(f'Exercise was not set. Error info: {err}')
