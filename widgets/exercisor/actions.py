from typing import Dict, Text, Union, Tuple, List
import numpy as np

from kivy.clock import mainthread, Clock

from .play.progress_counter import ProgressCounter
from .renderer import Renderer


class AbstractAction:
    """Implement basic functionality to control the state of the Exercisor Widget.

    Attributes
    ----------
    renderer : `renderer.Renderer`
        The basic renderer of the action. Each action has at least 1 renderer.
    controls : `controls.AbstractControls`
        The main buttons of the widget located at the bottom of the window.
    running : `bool`
        If `True` the action has been initialized.
    paused : `bool`
        The state of the action. If `True` the action is paused.
    """

    def __init__(self, renderer: Renderer, *args, **kwargs):
        self.renderer = renderer
        self.running = False
        self.paused = True

        # The controls is set and updated when the controls are created at the main window
        self.controls = None

    def initialize(self, smpl_mode: Text):
        """Reset the action's state, initialize the renderer and resume the action.

        Parameters
        ----------
        smpl_mode : `str` { 'smpl_mesh', 'smpl_kpnts' }
            Specify the type of rendering. It can be either the whole mesh or only the keypoints.
        """
        self.stop()
        self.running = True
        self.init_renderers(smpl_mode)
        self.resume()

    def init_renderers(self, smpl_mode: Text):
        """Setup the scene with the object :param: smpl_mode.

        Parameters
        ----------
        smpl_mode : `str` { 'smpl_mesh', 'smpl_kpnts' }
            Specify the type of rendering. It can be either the whole mesh or only the keypoints.
        """
        self.renderer.setup_scene(smpl_mode)

    @mainthread
    def render_mesh(
        self,
        renderer: Renderer = None,
        new_vertices: np.array = None,
        new_kpnts: np.array = None,
    ):
        """Display the vertices or keypoints on the renderer's canvas.

        Parameters
        ----------
        renderer : `renderer.Renderer`
            The default renderer of the action.
        new_vertices: `numpy.array`, (N x 3)
            The 3D coordinates of the mesh's N vertices.
        new_kpnts : `numpy.array`, (24 x 3)
            The 3D coordinates of the 24 SMPL keypoints.
        """
        if not type(renderer) == Renderer:
            return

        renderer.set_vertices(new_vertices, new_kpnts)

    def stop(self):
        """Clear the renderers' canvas and reset the buttons to their initial state."""
        self.running = False
        self.reset_renderers()
        if self.controls is not None:
            self.controls.reset_ui()

    def pause(self):
        """Pause the action and set the appropriate state to the play-pause button if it exists."""
        self.paused = True
        if hasattr(self.controls.ids, "play_pause_btn"):
            self.controls.ids.play_pause_btn.state = "normal"

    def resume(self):
        """Resume the action and set the appropriate state to the play-pause button if it exists."""
        self.paused = False
        if hasattr(self.controls.ids, "play_pause_btn"):
            self.controls.ids.play_pause_btn.state = "down"

    def reset_renderers(self):
        """Clear the renderers' canvases."""
        for r in self.renderer.parent.walk(restrict=True):
            if type(r) == Renderer:
                r.reset_scene()


class PlaybackAction(AbstractAction):
    """Implement the SMPL thread and renderer control.

    Attributes
    ----------
    smpl_thread : `smpl_thread.SMPLThread`
        The thread responsible for running the SMPL model and returning the output.
    keypoints_spec : `list` of `dict`
        The SMPL keypoints' specifications. The dictionaries contain the name and the parent of each keypoint.
    exercise : `numpy.array`, (N x 82)
        The SMPL's 82 thetas parameters of each of the N frames.
    """

    def __init__(
        self,
        smpl_thread,
        renderer: Renderer,
        keypoints_spec: List[Dict],
        *args,
        **kwargs,
    ):
        self.smpl_thread = smpl_thread
        super().__init__(renderer)
        self.renderer.single_click_handle = self.single_click_handle
        self.keypoints_spec = keypoints_spec

    def initialize(self, smpl_mode: Text, exercise: np.ndarray = None):
        """Set the SMPL thread's output function and the exercise data to use as input.

        Extends the :method:`initialize` of the :class:`AbstractAction`.

         Parameters
         ----------
         exercise : `numpy.array`, (N x 82)
             The SMPL's 82 thetas parameters of each of the N frames.
        """
        super().initialize(smpl_mode)

        self.smpl_thread.output_fn = self.render_mesh
        self.exercise = exercise
        self.smpl_thread.frame_index = 0

    @property
    def exercise(self):
        """The current playbacked exercise's thetas.

        When set, also sets the smpl thread's exercise.
        """
        return self._exercise

    @exercise.setter
    def exercise(self, new_exercise: np.ndarray):
        if new_exercise is not None:
            self._exercise = new_exercise
            self.smpl_thread.exercise = new_exercise

    @mainthread
    def render_mesh(
        self,
        new_vertices: np.ndarray = None,
        new_kpnts: np.array = None,
        frame: Dict = {},
    ):
        """Render the mesh and set the slider's frame index.

        Extends the :method: `render_mesh` of the :class: `AbstractAction`.

        Parameters
        ----------
        frame : `dict`
            Contains info regarding the processed frame, the current frame index and the timestamp it was received.
        """
        super().render_mesh(self.renderer, new_vertices, new_kpnts)
        if "index" in frame.keys():
            self.controls.frame_indx = frame["index"]

    def stop(self):
        """Stop the action and pause the SMPL thread."""
        super().stop()
        self.smpl_thread.pause()

    def pause(self):
        """Pause the action and the SMPL thread."""
        super().pause()
        self.smpl_thread.pause()

    def resume(self):
        """Resume the action and the SMPL thread."""
        super().resume()
        self.smpl_thread.resume()

    def seek(self, time_point: Union[int, float], fmt: Text = "frame"):
        """Set the playback at a specific point. The thread is resumed and instantly paused so that it will run only once.

        Parameters
        ----------
        time_point : `int` or `float`
            The point in time from which the playback will continue.
        fmt : `str` { 'frame', 'duration' }
            Specifies if the :param: `time_point` is the frame index from where to continue
            or the fast-forward/rewind duration in seconds.
        """
        if fmt == "duration":
            time_point = (
                self.smpl_thread.frame_index + self.smpl_thread.target_fps * time_point
            )

        self.smpl_thread.frame_index = time_point
        self.controls.frame_indx = time_point
        self.resume()
        self.pause()

    def single_click_handle(self, touch_pos: Tuple[float, float], closest_kpnt: str):
        """Display the keypoing edit form at the clicked position.

        Parameters
        ----------
        touch_pos : `tuple` [`float`, `float`]
            The position of the click in window coordinates.
        closest_kpnt : `str`
            The name of the closest keypoint to the click position.
        """
        if not self.running:
            return

        self.controls.display_kpnt_edit_form(closest_kpnt, self.keypoints_spec)


class PredictAction(AbstractAction):
    """Implement the HMR thread and renderer control.

    Attributes
    ----------
    hmr_thread : `hmr_thread.HMRThread`
        The thread responsible for running the HMR model and returning the output.
    """

    def __init__(self, hmr_thread, renderer: Renderer, *args, **kwargs):
        self.hmr_thread = hmr_thread
        super().__init__(renderer)

    def initialize(
        self, smpl_mode: Text, source: Text = None, save_exercise: bool = False
    ):
        """Set the HMR thread's output function and the source of the input video.

        Extends the :method: `initialize` of the :class: `AbstractAction`.

        Parameters
        ----------
        source : `str`
            The source of the video to use as input. It can be `cam` for camera input or a path to a local video file.
        save_exercise : `bool`
            Whether to save the predicted exercises' data.
        """
        super().initialize(smpl_mode)

        self.hmr_thread.output_fn = self.render_mesh
        if source is not None:
            self.hmr_thread.capture = source
        if save_exercise:
            self.hmr_thread.save()

    @mainthread
    def render_mesh(
        self, new_vertices: np.ndarray = None, new_kpnts: np.ndarray = None
    ):
        """Extends the :method: `render_mesh` of the :class: `AbstractAction`."""
        super().render_mesh(self.renderer, new_vertices, new_kpnts)

    def stop(self):
        """Stop the action and pause the HMR thread."""
        super().stop()
        self.hmr_thread.pause()

    def pause(self):
        """Pause the action and the HMR thread"""
        super().pause()
        self.hmr_thread.pause()

    def resume(self):
        """Resume the action and the HMR thread"""
        super().resume()
        self.hmr_thread.resume()


class PlayAction(AbstractAction):
    """Control the main play functionality of the Exercisor.

    Use both SMPL and HMR threads to playback an exercise and predict from the camera respectively.
    Both threads render on their respective renderers. A third renderer is used to render the keypoint error vectors.
    The keypoint error vectors are calculated and displayed as a moving average on the last frames.
    For the HMR thread, a frame smoothing is implemented on its output to smooth the outlier frames.
    A widget is displayed that either counts the repetitions or functions as a countdown depending on the exercise.

    Attributes
    ----------
    threads : `dict` [`str`, { `smpl_thread.SMPLThread`, `hmr_thread.HMRThread }]
        The thread responsible for running the SMPL model and returning the output.
    renderer : `renderer.Renderer`
        The renderer to display the SMPL thread's output of the playbacked exercise.
    pred_renderer : `renderer.Renderer`
        The renderer to display the HMR thread's output of the user's camera.
    error_renderer : `renderer.Renderer`
        The renderer to display the keypoint error vectors when the :attr: `renderer` and
        :attr: `pred_renderer`'s outputs are misaligned.
    """

    def __init__(self, threads: Dict, renderers: List[Renderer], *args, **kwargs):
        self.threads = threads
        renderer, self.pred_renderer, self.error_renderer = renderers
        self.error_renderer.canvas["object_color"] = (
            1.0,
            0.0,
            0.0,
        )  # the error vectors default red color
        super().__init__(renderer)

        self._error_sample_win = (
            5  # the number of frames for the moving average of the error vectors
        )
        self._smooth_sample_win = (
            3  # the number of frames for the HMR's smoothing average
        )
        self._prev_kpnts = np.empty(shape=(0, 24, 3))

        self._progress_counter = ProgressCounter(
            stop_action=self.stop
        )  # the timer/counter widget

    def initialize(self, smpl_mode: Text, metadata: Dict, thetas: np.ndarray = None):
        """Setup the HMR and SMPL threads and the timer/counter widget.

        Extends the :method: `initialize` of the :class: `AbstractAction`.

        Parameters
        ----------
        smpl_mode: `str` {'smpl_mesh', 'smpl_kpnts'}
            The display mode of the smpl playback.
        metadata: `dict`
            Store metadata regarding the current exercise.
        thetas: `numpy.ndarray`, (N x 85)
            The 85 smpl parameters for each of the N frames of the exercise.
        """
        super().initialize(smpl_mode)

        self.threads["smpl"].output_fn = self.render_correct_mesh
        self.threads["hmr"].output_fn = self.process_predictions

        # Prepare the SMPL playback
        if thetas is not None:
            self._thetas = thetas
            self.threads["smpl"].exercise = thetas
            self.threads["smpl"].frame_index = 0
        # Prepare the HMR predictions
        self.threads["hmr"].capture = "cam"

        # Set up the progress counter depending on the exercise
        self.renderer.parent.add_widget(self._progress_counter)
        Clock.schedule_once(self._setup_progress_counter)
        self._rep_count = 0
        self._start_new_rep()

    def _setup_progress_counter(self, opts: Dict = None):
        """Setup the progress counter widget depending on the options of the exercise.

        Parameters
        ----------
        opts: dict
            Provides the settings for the progress widget like the type {'timer', 'counter'} and the the max count.
        """
        self._progress_counter.mode = "repetition"
        self._progress_counter.max_count = 5  # the desired reps + 1
        self._progress_counter.counter = 1

        # The following will be removed when exercise data are setup. For the time being, these are used for testing.
        if self._progress_counter.mode == "timer":
            self._progress_counter.max_count = 10
            self._progress_counter.counter = 10

    def init_renderers(self, smpl_mode: Text):
        """Setups the :attr: `pred_renderer` with the opposite :param: `smpl_mode`.

        Extends the :method: `init_renderers` of the :class: `AbstractAction`.
        """
        super().init_renderers(smpl_mode)
        self.pred_renderer.setup_scene(
            "smpl_mesh" if smpl_mode == "smpl_kpnts" else "smpl_kpnts"
        )

    def _start_new_rep(self):
        """Reset all per repetition variables and increase the repetition count."""
        self._rep_count += 1  # the total number of repetitions
        if self._progress_counter.mode == "repetition":
            self._progress_counter.counter += 1

        self._pred_frm_indx = (
            0  # the number of performed predictions for the current repetition
        )
        self._finished_rep = False  # indicates when the repetition is finished

        # Stores all correct keypoints from the SMPL thread
        self._kpnts_mat = np.zeros((self._thetas.shape[0], 24, 3), dtype=np.float32)

        # Stores all the keypoint errors for each HMR prediction
        self._kpnt_err_vecs = np.zeros((self._thetas.shape[0], 24, 3), dtype=np.float32)

        self.error_renderer.reset_scene()  # clear the error vectors

    @mainthread
    def render_correct_mesh(
        self,
        correct_verts: np.ndarray = None,
        correct_kpnts: np.ndarray = None,
        frame: Dict = None,
    ):
        if self._thetas.shape[0] < frame["index"]:
            # The incoming frame is from previous exercise
            return

        super().render_mesh(self.renderer, correct_verts, correct_kpnts)

        self._kpnts_mat[frame["index"], :, :] = correct_kpnts
        self._corr_frm_indx = frame["index"]
        if frame["index"] == self._thetas.shape[0] - 1:
            # When the frame index of the smpl thread reached max, the repetition has ended
            self._finished_rep = True

    @mainthread
    def process_predictions(self, predicted_verts=None, predicted_kpnts=None):
        try:
            correct_kpnts = self._kpnts_mat[self._corr_frm_indx, :, :]
        except IndexError:
            return

        predicted_kpnts = self._smooth_kpnts(predicted_kpnts)

        self._kpnt_err_vecs[self._pred_frm_indx, :, :] = correct_kpnts - predicted_kpnts

        # If there are enough samples render the error vectors
        if self._pred_frm_indx >= self._error_sample_win:
            self._render_error_vectors(predicted_kpnts, self._pred_frm_indx)

        # Render the predicted output
        super().render_mesh(self.pred_renderer, predicted_verts, predicted_kpnts)
        self._pred_frm_indx += 1

        if self._finished_rep:
            self._end_rep()
            self._start_new_rep()

    def _smooth_kpnts(self, curr_kpnts):
        """Smooth the predicted keypoints by implementing a moving average window."""
        verts = np.append(
            self._prev_kpnts, np.expand_dims(curr_kpnts, axis=0), axis=0
        ).mean(axis=0, keepdims=True)
        self._prev_kpnts = np.append(self._prev_kpnts, verts, axis=0)
        if self._prev_kpnts.shape[0] == self._smooth_sample_win:
            self._prev_kpnts = np.delete(self._prev_kpnts, 0, axis=0)

        return verts[0]

    def _render_error_vectors(self, predicted_kpnts, indx):
        """Display the error on the keypoints

        Parameters
        ----------
        predicted_kpnts : array_like (24 x 3)
            The predicted keypoints of the currect frame
        correct_kptns : array_like (24 x 3)
            The correct keypoints of the currect frame
        """
        error_vectors = self._kpnt_err_vecs[
            indx - self._error_sample_win : indx, :, :
        ].mean(axis=0)

        distances = np.linalg.norm(error_vectors, axis=1)
        max_indices = np.argwhere(distances > 0.3).flatten()

        opts = {
            "start_verts": predicted_kpnts[max_indices],
            "direction_vecs": error_vectors[max_indices],
        }

        self.error_renderer.reset_scene()
        if self.running:
            self.error_renderer.setup_scene("error_vectors", opts)

    def _end_rep(self):
        """Calculate the errors and play the feedback animations"""
        rep_mse = np.square(self._kpnt_err_vecs).mean()
        # kpnts_mse = np.square(self._kpnt_err_vecs).mean(axis=0)
        if rep_mse < 0.015:
            self.renderer.play_animation("correct_repetition")

        print(f"Repetition: {self._rep_count} , total error: {rep_mse}")

    def demo_render(self, rendered_obj):
        self.stop()
        self.running = True
        super().init_renderers(rendered_obj)

    def stop(self):
        super().stop()
        for thread in self.threads.values():
            thread.pause()
        self.renderer.parent.remove_widget(self._progress_counter)

    def pause(self):
        super().pause()
        for thread in self.threads.values():
            thread.pause()

    def resume(self):
        super().resume()
        for thread in self.threads.values():
            thread.resume()
