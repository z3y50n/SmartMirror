import errno
import os
import threading

import cv2
import numpy as np
import tensorflow as tf

from .ml_thread import MLThread
from .hmr_model import HMR
from .utils.preprocess import process_image


class HMRThread(MLThread):
    """
    Creates a thread that will load the HMR model.

    Attributes
    ----------
    model_cfg: `module`
        The configuration options for the HMR model.
    img_size: `int`
        The size in pixels of both dimensions of the input image.
    output_fn: `callable`
        The function to call on the outputs for each prediction.
    save_fn: `callable`
        Saves the predicted outputs for a specific exercise.
    graph: `tensorflow.Graph`
        The computational graph to be used.
    sess: `tensorflow.Session`
        The session to be used.
    model: `models.HMR`
        The HMR model implementation in tensorflow.
    thetas: `list` [`lists`], (N x 82)
        The 82 thetas for each frame to be saved when saving an exercise.
    source: `str`
        The source stream to be used in the capture. Can be either 'cam' or a video file path.
    """

    def __init__(self, model_cfg, save_fn, *args, **kwargs):
        # Setup the session and load the hmr model
        self.model_cfg = model_cfg
        self.img_size = model_cfg.img_size
        self.save_fn = save_fn

        self._cap_source = ""
        self.capture = "cam"

        self._saving = threading.Event()
        super().__init__("HMR", *args, **kwargs)

    def _prepare_model(self):
        """Create the tensorflow graph and session and load the model"""
        self.graph = tf.Graph()
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.compat.v1.Session(graph=self.graph, config=config)
        with self.graph.as_default():
            self.model = self.load_model()

    def load_model(self):
        """Load the HMR model"""
        model = HMR(self.model_cfg, sess=self.sess)
        self.thetas = []
        return model

    def _prepare_inputs(self):
        """
        Get the next frame from the capture and preprocess the frame image.

        Returns
        -------
        `dict`
            Contains the retrieval status and the current frame image.
            The retrieval status is a `bool`, which is `True` if the frame retrieval was successful, `False` otherwise.
            The frame image is an `numpy.ndarray`.
        """
        ret, frame = self.capture.read()

        if ret:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)

            frame, _ = process_image(frame, self.img_size)
        inputs = {"ret": ret, "frame": frame}
        return inputs

    def _predict(self, inputs: np.ndarray):
        """Display the input frame image and return the predictions, if the frame retrieval was successful.

        Parameters
        ----------
        inputs : `dict`
            The returned dict of :method: `prepare_inputs` as described above.

        Returns
        -------
        `dict`
            The vertices and keypoints of the smpl mesh if the frame retrieval was successful.
            If it was saving an exercise, at the end of the exercise returns the thetas for the whole exercise.
        """
        if inputs["ret"]:
            joints, verts, cams, joints3d, theta = self.model.predict(
                inputs["frame"], get_theta=True
            )

            if self._saving.is_set():
                self.thetas.append(theta[0, 3:])

            outputs = {"verts": verts[0], "joints3d": joints3d[0]}
            return outputs
        else:
            if self._saving.is_set():
                self._saving.clear()
                thetas = np.array(self.thetas)
                self.thetas = []
                self.pause()
                return {"thetas": thetas}

    def _process_outputs(self, outputs: dict):
        """Depending on the type of output, save the exercise data or send the outputs to the renderer.

        Parameters
        ----------
        outputs : `dict`
            The outputs are the returned value of the :method: `predict`.
        """
        if outputs is None:
            return
        if "thetas" in outputs.keys():
            filename = os.path.basename(self._cap_source)
            filename = os.path.splitext(filename)[0]
            self.save_fn(filename, outputs["thetas"])
        elif "verts" in outputs.keys() and "joints3d" in outputs.keys():
            self.output_fn(outputs["verts"], outputs["joints3d"])

    def _cleaning_up(self):
        """Release the acquired capture and close the opencv windows."""
        self.capture.release()
        cv2.destroyAllWindows()

    def pause(self):
        """Close all the opencv windows."""
        cv2.destroyAllWindows()
        super().pause()

    def save(self):
        self.thetas = []
        self._saving.set()

    @property
    def capture(self):
        """`cv2.VideoCapture`: The video capture stream.

        The capture source can be either 'cam' or a specified video file.

        Raises
        ------
        FileNotFoundError
            If the capture source was a video file and no file was found on that path.
        """
        return self._capture

    @capture.setter
    def capture(self, source):
        if self._cap_source == source:
            return

        self._cap_source = source
        if self._cap_source == "cam":
            self._capture = cv2.VideoCapture(2)
        else:
            if os.path.exists(self._cap_source):
                self._capture = cv2.VideoCapture(self._cap_source)
            else:
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), self._cap_source
                )
