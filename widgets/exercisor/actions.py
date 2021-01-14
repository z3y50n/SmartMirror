

class PlaybackAction:

    def __init__(self, thread, init_scene, reset_ui, *args, **kwargs):
        self.thread = thread
        self.init_scene = init_scene
        self.reset_ui = reset_ui
        self.running = False
        self.paused = False

    def initialize(self, smpl_mode, exercise=None):
        self.reset_ui()
        self.running = True
        self.init_scene(smpl_mode)
        if exercise is not None:
            self.thread.exercise = exercise

    def stop(self):
        self.running = False
        self.thread.pause()

    def pause(self):
        self.paused = True
        self.thread.pause()

    def resume(self):
        self.paused = False
        self.thread.resume()

    def seek(self, new_frame_indx):
        self.pause()
        self.thread.frame_index = new_frame_indx
        self.resume()


class PredictAction:

    def __init__(self, thread, init_scene, reset_ui, *args, **kwargs):
        self.thread = thread
        self.init_scene = init_scene
        self.reset_ui = reset_ui
        self.running = False
        self.paused = False

    def initialize(self, smpl_mode, source=None, saving=False):
        self.reset_ui()
        self.running = True
        self.init_scene(smpl_mode)
        if source is not None:
            self.thread.capture = source
        if saving:
            self.thread.save()

    def stop(self):
        self.running = False
        self.thread.pause()

    def pause(self):
        self.paused = True
        self.thread.pause()

    def resume(self):
        self.paused = False
        self.thread.resume()


class PlayAction:

    def __init__(self, threads, *args, **kwargs):
        self.threads = threads
