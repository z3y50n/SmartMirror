from abc import ABC, abstractclassmethod
import threading
import time
from log import logger


class MLThread(ABC, threading.Thread):
    """
    """
    def __init__(self, model_name=None, target_fps=25, *args, **kwargs):
        super(MLThread, self).__init__(*args, **kwargs)

        self.model_name = model_name
        self.name = self.model_name + '_Thread'
        self.target_fps = target_fps

        self._resumed = threading.Event()
        self._running = threading.Event()
        self._running.set()
        self.start()

    def pause(self):
        self._resumed.clear()

    def resume(self):
        self._resumed.set()

    def stop(self):
        self._running.clear()

    def is_paused(self):
        return not self._resumed.is_set()

    def run(self, *args, **kwargs):

        self.prepare_model()
        logger.info(f'Loaded the {self.model_name} model.. Waiting to resume..')

        while(self._running.is_set()):
            self._resumed.wait()
            start = time.time()
            inputs = self.prepare_inputs()
            outputs = self.predict(inputs)
            self.process_outputs(outputs)
            time.sleep(max(1./self.target_fps - (time.time() - start), 0))

        self.cleaning_up()
        logger.info(f'{self.name} has finished execution')

    @abstractclassmethod
    def prepare_model(self):
        pass

    @abstractclassmethod
    def prepare_inputs(self):
        pass

    @abstractclassmethod
    def predict(self):
        pass

    @abstractclassmethod
    def process_outputs(self):
        pass

    @abstractclassmethod
    def cleaning_up(self):
        pass
