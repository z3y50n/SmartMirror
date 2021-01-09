from abc import ABC, abstractclassmethod
import threading
import logging

import tensorflow as tf


class MLThread(ABC, threading.Thread):
    """
    """
    def __init__(self, *args, **kwargs):
        super(MLThread, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):

        self.graph = tf.Graph()
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.compat.v1.Session(graph=self.graph, config=config)

        with self.graph.as_default():
            self.model = self.load_model()

    @abstractclassmethod
    def load_model(self):
        logging.info(f'Loading the {self.name} model')
        pass

    @abstractclassmethod
    def predict(self):
        pass
