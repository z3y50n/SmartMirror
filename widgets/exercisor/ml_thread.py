from abc import ABC, abstractclassmethod
import threading
import time
from .utils.log import logger


class MLThread(ABC, threading.Thread):
    """The abstract implementation of a machine learning module that will be run on a separate thread.

    The thread executes instantly when it is constructed so that the model will start loading
    and then it enters the paused state.

    Attributes
    ----------
    model_name : `str`
        The name of the AI model that will be executed.
    name : `str`
        The name of the thread.
    target_fps : `int`
        The maximum number of predictions per second.
    """

    def __init__(self, model_name=None, target_fps=25, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_name = model_name
        self.name = self.model_name + "Thread"
        self.daemon = True

        self.target_fps = target_fps
        self.output_fn = None

        self._resumed = threading.Event()
        self._running = threading.Event()
        self._running.set()
        self.start()

    def pause(self):
        """Pauses the execution of the thread."""
        self._resumed.clear()

    def resume(self):
        """Resumes the execution of the thread."""
        self._resumed.set()

    def stop_exec(self):
        """Stops the execution of the thread."""
        self._running.clear()

    def is_paused(self):
        """Returns `True` if the thread is paused, `False` otherwise."""
        return not self._resumed.is_set()

    def run(self, *args, **kwargs):
        """The execution method of the thread."""
        logger.info(f"Loading {self.model_name}...")
        self._prepare_model()
        logger.info(f"Loaded the {self.model_name} model")

        while self._running.is_set():
            self._resumed.wait()
            self._start_time = time.time()
            inputs = self._prepare_inputs()
            outputs = self._predict(inputs)
            self._process_outputs(outputs)

            # If processing finished fast, sleep to guarantee the target_fps
            time.sleep(max(1.0 / self.target_fps - (time.time() - self._start_time), 0))

        self._cleaning_up()
        logger.info(f"{self.name} has finished execution")

    @abstractclassmethod
    def _prepare_model(self):
        """Prepare and load the AI model."""
        pass

    @abstractclassmethod
    def _prepare_inputs(self):
        """Prepare the inputs that will be used in the current prediction."""
        pass

    @abstractclassmethod
    def _predict(self):
        """Use the inputs to predict the outputs."""
        pass

    @abstractclassmethod
    def _process_outputs(self):
        """Process the outputs and/or use them."""
        pass

    @abstractclassmethod
    def _cleaning_up(self):
        """Release the acquired resources when the prediction loop finishes."""
        pass
