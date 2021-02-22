import operator
import numpy as np

from kivy.clock import mainthread
from renderer import Renderer


class AbstractAction():

    def __init__(self, renderer, *args, **kwargs):
        self.renderer = renderer
        self.controls = None
        self.running = False
        self.paused = True
        # self._sampl_wind = 5
        # self._prev_verts = np.empty(shape=(0, 6890, 3))

    def initialize(self, smpl_mode):
        self.stop()
        self._nframes = 0
        self.running = True
        self.init_renderers(smpl_mode)

    def init_renderers(self, smpl_mode):
        self.renderer.setup_scene(smpl_mode)

    @mainthread
    def render_mesh(self, renderer=None, new_vertices=None, new_kpnts=None):
        if not type(renderer) == Renderer:
            return

        recalc_normals = False
        if self._nframes == 0:
            recalc_normals = True
        if renderer.curr_obj == 'smpl_mesh':
            # new_vertices = self._smooth_verts(new_vertices)
            renderer.set_vertices(new_vertices, recalc_normals)
        elif renderer.curr_obj == 'smpl_kpnts':
            renderer.set_vertices(new_kpnts)

        self._nframes += 1

    # Smoothing over vertices
    # def _smooth_verts(self, curr_verts):
    #     verts = np.append(self._prev_verts, np.expand_dims(curr_verts, axis=0), axis=0).mean(axis=0, keepdims=True)
    #     self._prev_verts = np.append(self._prev_verts, verts, axis=0)
    #     if self._prev_verts.shape[0] == self._sampl_wind:
    #         self._prev_verts = np.delete(self._prev_verts, 0, axis=0)

    #     return verts[0]

    def stop(self):
        self.running = False
        self.reset_renderers()
        self.controls.reset_buttons()

    def pause(self):
        self.paused = True
        if hasattr(self.controls.ids, 'play_pause_btn'):
            self.controls.ids.play_pause_btn.state = 'normal'

    def resume(self):
        self.paused = False
        if hasattr(self.controls.ids, 'play_pause_btn'):
            self.controls.ids.play_pause_btn.state = 'down'

    def reset_renderers(self):
        for r in self.renderer.parent.walk(restrict=True):
            if type(r) == Renderer:
                r.reset_scene()


class PlaybackAction(AbstractAction):

    def __init__(self, smpl_thread, renderer, *args, **kwargs):
        self.smpl_thread = smpl_thread
        super().__init__(renderer)

    def initialize(self, smpl_mode, exercise=None):
        super().initialize(smpl_mode)

        self.smpl_thread.output_fn = self.render_mesh
        if exercise is not None:
            self.smpl_thread.exercise = exercise

    @mainthread
    def render_mesh(self, new_vertices=None, new_kpnts=None, frame: dict = {}):
        super().render_mesh(self.renderer, new_vertices, new_kpnts)
        if 'index' in frame.keys():
            self.controls.frame_indx = frame['index']

    def stop(self):
        super().stop()
        self.smpl_thread.pause()

    def pause(self):
        super().pause()
        self.smpl_thread.pause()

    def resume(self):
        super().resume()
        self.smpl_thread.resume()

    def seek(self, time_point, fmt='frame'):
        """ Set the playback at a specific point. The thread is resumed and instantly paused so that it will run only once

        Parameters
        ----------
        time_point : int or float
            The point in time from which the playback will continue.
        fmt : { 'frame', 'duration' }
            Specifies if the :param: time_point is the frame index from where to continue
            or the fast-forward/rewind duration.
        """
        if fmt == 'duration':
            time_point = self.smpl_thread.target_fps * time_point

        self.smpl_thread.frame_index = time_point
        self.controls.frame_indx = time_point
        self.resume()
        self.pause()


class PredictAction(AbstractAction):

    def __init__(self, hmr_thread, renderer, *args, **kwargs):
        self.hmr_thread = hmr_thread
        super().__init__(renderer)

    def initialize(self, smpl_mode, source=None, save_exercise=False):
        super().initialize(smpl_mode)

        self.hmr_thread.output_fn = self.render_mesh
        if source is not None:
            self.hmr_thread.capture = source
        if save_exercise:
            self.hmr_thread.save()

    @mainthread
    def render_mesh(self, new_vertices=None, new_kpnts=None, frame=None):
        super().render_mesh(self.renderer, new_vertices, new_kpnts)

    def stop(self):
        super().stop()
        self.hmr_thread.pause()

    def pause(self):
        super().pause()
        self.hmr_thread.pause()

    def resume(self):
        super().resume()
        self.hmr_thread.resume()


class PlayAction(AbstractAction):

    def __init__(self, threads, renderers, *args, **kwargs):
        self.threads = threads
        renderer, self.pred_renderer, self.error_renderer = renderers
        super().__init__(renderer)
        self.error_frame_window = 10

    def initialize(self, smpl_mode, exercise=None):
        super().initialize(smpl_mode)

        self.threads['smpl'].output_fn = self.render_correct_mesh
        self.threads['hmr'].output_fn = self.process_predictions

        if exercise is not None:
            self.exercise = exercise
            self.threads['smpl'].exercise = exercise
        self.threads['hmr'].capture = 'cam'

        self.rep_count = 0
        self._start_new_rep()

    def init_renderers(self, smpl_mode):
        super().init_renderers(smpl_mode)
        self.pred_renderer.setup_scene('smpl_mesh' if smpl_mode == 'smpl_kpnts' else 'smpl_kpnts')

    def _start_new_rep(self):
        self.rep_count += 1
        self.frame_index = 0
        self._finished_rep = False
        self._kpnts_mat = np.zeros((24, 3, self.exercise.shape[0]), dtype=np.float32)
        self._kpnt_err_vecs = np.zeros((24, 3, self.exercise.shape[0]), dtype=np.float32)
        self._smpl_frm_tmstamps = np.zeros((self.exercise.shape[0]), dtype=np.float32)

    @mainthread
    def render_correct_mesh(self, correct_verts=None, correct_kpnts=None, frame=None):
        super().render_mesh(self.renderer, correct_verts, correct_kpnts)

        if self._smpl_frm_tmstamps.shape[0] > frame['index']:
            # Makes sure that the recieved frame is not from a previous exercise
            self._smpl_frm_tmstamps[frame['index']] = frame['timestamp']
            self._kpnts_mat[:, :, frame['index']] = correct_kpnts

        if frame['index'] < self.frame_index:
            self._finished_rep = True

    @mainthread
    def process_predictions(self, predicted_verts=None, predicted_kpnts=None, pred_tmstamp=None):
        if not self._smpl_frm_tmstamps.any():
            return

        correct_kpnts = self._get_keypoints_from_correct_frame(pred_tmstamp)

        self._kpnt_err_vecs[:, :, self.frame_index] = (correct_kpnts - predicted_kpnts)

        # Calculate the momentary keypoint error vector
        if self.frame_index >= self.error_frame_window:
            momen_kpnt_err_vec = self._kpnt_err_vecs[:, :, self.frame_index - self.error_frame_window:].mean(axis=2)
            self._render_error_vectors(momen_kpnt_err_vec, predicted_kpnts)

        # Render the predicted output
        super().render_mesh(self.pred_renderer, predicted_verts, predicted_kpnts)
        self.frame_index += 1

        if self._finished_rep:
            self._end_rep()
            self._start_new_rep()

    def _get_keypoints_from_correct_frame(self, pred_timestamp):
        """ Return the keypoints that correspond to the predicted frame's timestamp """
        tm_diffs = [abs(pred_timestamp - corr_tmstamp) for corr_tmstamp in self._smpl_frm_tmstamps]
        min_diff_indx = tm_diffs.index(min(tm_diffs))
        return self._kpnts_mat[:, :, min_diff_indx]

    def _render_error_vectors(self, error_vectors, predicted_kpnts):
        """ Display the error on the keypoints

        Parameters
        ----------
        error_vectors : array_like ()
            The error vectors starting from :param: predicted_kpnts and direction to the correct keypoints
        predicted_kpnts : array_like (24 x 3)
            The predicted keypoints of the currect frame
        """
        distances = np.linalg.norm(error_vectors, axis=1)
        d = {indx: val for indx, val in enumerate(distances.tolist())}
        sorted_d = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
        max_dists_indices = [k[0] for k in sorted_d][:3]

        self.error_renderer.render_error_vectors(predicted_kpnts[max_dists_indices], error_vectors[max_dists_indices])

    def _end_rep(self):
        """ Calculate the errors and play the feedback animations """
        rep_mse = np.square(self._kpnt_err_vecs).mean()
        kpnts_mse = np.square(self._kpnt_err_vecs).mean(axis=2)
        if rep_mse < 0.03:
            self.renderer.play_animation('correct_repetition')

        print(f'Repetition: {self.rep_count} , total error: {rep_mse}')

    def demo_render(self, rendered_obj):
        self.stop()
        self.running = True
        super().init_renderers(rendered_obj)

    def stop(self):
        for thread in self.threads.values():
            thread.pause()
        super().stop()

    def pause(self):
        super().pause()
        for thread in self.threads.values():
            thread.pause()

    def resume(self):
        super().resume()
        for thread in self.threads.values():
            thread.resume()
