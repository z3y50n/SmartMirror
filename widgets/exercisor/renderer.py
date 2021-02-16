import numpy as np
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty
from kivy.resources import resource_find
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import glEnable, glDisable, GL_DEPTH_TEST
from kivy.graphics import RenderContext, Callback, PushMatrix, PopMatrix, \
    Translate, Rotate, Mesh, UpdateNormalMatrix, Scale

from play.mesh_utils import ObjFile, CustomMeshData
from quaternion import quaternion_to_euler, euler_to_quaternion, quat_mult, euler_to_roll_pitch_yaw


class Renderer(Widget):

    MESH_MODES = ('points', 'line_strip', 'line_loop', 'lines', 'triangles', 'triangle_strip', 'triangle_fan')
    curr_mode = StringProperty('')
    nframes = NumericProperty(-1)
    zoom_speed = 0.03

    __slots__ = ['smpl_faces_path', 'obj_mesh_path']

    def __init__(self, smpl_faces_path=None, obj_mesh_path=None):

        if smpl_faces_path is not None:
            self.smpl_faces = np.load(smpl_faces_path)

        if obj_mesh_path is not None:
            self.scene = ObjFile(obj_mesh_path)

        # Make a canvas and add simple view
        self.canvas = RenderContext(compute_normal_mat=True)
        self.canvas.shader.source = resource_find('simple.glsl')
        self.canvas['object_color'] = (0.93, 0.74, 0.71)
        self.canvas['diffuse_light'] = (1.0, 0.7, 0.8)
        self.canvas['ambient_light'] = (0.1, 0.1, 0.1)
        super().__init__()

        self.create_mesh_fn = {
            'monkey': self.create_monkey_mesh,
            'monkey_no_norms': self.create_monkey_mesh_no_norms,
            'random': self.create_rand_mesh,
            'smpl_mesh': self.create_smpl_mesh,
            'smpl_kpnts': self.create_smpl_kpnts,
        }

        self.animations = {
            'scale': self.scale_anim,
            'rotate': self.rotate_anim,
            'deform': self.deform_anim
        }

        self.curr_mode = 'triangles'
        self.curr_obj = None
        self.timers = {}
        self.nframes = 0
        self.reset_scene()
        self.store_quat = None
        self.Dx, self.Dy = 0, 0

    def setup_scene(self, rendered_obj):
        self.curr_obj = rendered_obj
        with self.canvas:
            self.cb = Callback(self._setup_gl_context)
            PushMatrix()
            self.trans = Translate(0, 0, -3)
            self.roty = Rotate(1, 0, 1, 0)
            self.rotx = Rotate(1, 1, 0, 0)
            self.scale = Scale(1, 1, 1)

            self.yaw = Rotate(0, 0, 0, 1)
            self.pitch = Rotate(0, -1, 0, 0)
            self.roll = Rotate(0, 0, 1, 0)
            self.quat = euler_to_quaternion([0, 0, 0])

            UpdateNormalMatrix()
            if rendered_obj in self.create_mesh_fn.keys():
                self.create_mesh_fn[rendered_obj]()
            PopMatrix()
            self.cb = Callback(self._reset_gl_context)

        self._update_glsl()

    def _setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)

    def _reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def _update_glsl(self):
        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-asp, asp, -1, 1, 1.5, 100, 1)
        self.canvas['projection_mat'] = proj

    def reset_scene(self):
        self.canvas.clear()
        self._reset_timers(('scale', 'rotate', 'deform'))

        self.nframes = 0

    def _reset_timers(self, timer_spec):
        for timer in timer_spec:
            if timer in self.timers.keys():
                self.timers[timer].cancel()

    def create_monkey_mesh(self):
        m = list(self.scene.objects.values())[0]
        self.mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            mode=self.curr_mode,
        )
        self.mesh_data = CustomMeshData(vertices=m.verts_raw, faces=m.faces)
        self.mesh_data.gl_verts = m.vertices
        self.mesh_data.indices = m.indices

    def create_monkey_mesh_no_norms(self):
        m = list(self.scene.objects.values())[0]
        self.mesh_data = CustomMeshData(vertices=m.verts_raw, faces=m.faces)
        self.mesh_data.init_gl_verts()
        self.mesh = Mesh(
            vertices=self.mesh_data.gl_verts,
            indices=self.mesh_data.indices,
            fmt=self.mesh_data.vertex_format,
            mode=self.curr_mode
        )

    def create_rand_mesh(self):
        verts = np.random.logistic(scale=0.5, size=(10000, 3))
        # verts = np.random.normal(scale=0.7, size=(10000, 3))
        # verts = np.random.laplace(scale=0.6, size=(10000, 3))
        # verts = np.random.lognormal(size=(10000, 3))

        self.mesh_data = CustomMeshData(vertices=verts, faces=self.smpl_faces)
        self.mesh_data.init_gl_verts()
        self.mesh = Mesh(
            vertices=self.mesh_data.gl_verts,
            indices=self.mesh_data.indices,
            fmt=self.mesh_data.vertex_format,
            mode=self.curr_mode
        )

    def create_smpl_mesh(self):
        verts = np.random.rand(6890, 3) * 2 - 1
        self.mesh_data = CustomMeshData(vertices=verts, faces=self.smpl_faces)
        self.mesh_data.init_gl_verts()
        self.curr_mode = 'triangles'
        self.mesh = Mesh(
            vertices=self.mesh_data.gl_verts,
            indices=self.mesh_data.indices,
            fmt=self.mesh_data.vertex_format,
            mode=self.curr_mode
        )
        self.rotx.angle += 180

    def create_smpl_kpnts(self):
        self.mesh_data = CustomMeshData()
        verts = np.random.rand(24, 3) * 2 - 1
        verts_formatted = np.concatenate((verts, -np.ones(shape=(24, 3)), np.zeros(shape=(24, 2))), axis=1)
        indices = []
        parents = [-1,  0,  0,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  9,  9, 12, 13, 14, 16, 17, 18, 19, 20, 21]
        for indx, kpnt in enumerate(parents):
            if kpnt < 0:
                continue
            indices.extend([kpnt, indx])

        self.mesh_data.verts_formatted = verts_formatted
        self.mesh_data.indices = indices
        self.mesh_data.gl_verts = verts_formatted.flatten().tolist()
        self.curr_mode = 'lines'
        self.mesh = Mesh(
            vertices=self.mesh_data.gl_verts,
            indices=self.mesh_data.indices,
            fmt=self.mesh_data.vertex_format,
            mode=self.curr_mode
        )
        self.rotx.angle += 180

    def animate_mesh(self, anim, play):
        if not hasattr(self, 'mesh'):
            raise UnboundLocalError('The mesh does not exist')

        if anim in self.animations.keys():
            self._reset_timers((anim,))
            if play:
                self.timers[anim] = Clock.schedule_interval(self.animations[anim], 1/60.)

    def scale_anim(self, delta):
        step = ((self.nframes) % 360) * np.pi / 180.
        scale_factors = (np.sin(step) * 0.7 + 0.9, -np.sin(step) * 0.7 + 0.9, 1)
        self.scale.xyz = scale_factors

    def rotate_anim(self, delta):
        self.roty.angle += delta * 50

    def deform_anim(self, delta):
        vertices = self.mesh_data.vertices + np.random.normal(size=self.mesh_data.vertices.shape) * 0.02
        self.set_vertices(vertices)

    def set_vertices(self, vertices):
        if not hasattr(self, 'mesh'):
            return

        if self.curr_obj == 'smpl_mesh' and self.nframes == 0:
            self.mesh_data.vertices = vertices
            self.mesh_data.init_gl_verts()

        self.mesh_data.update_verts(vertices)
        self.mesh.vertices = self.mesh_data.gl_verts
        self.nframes += 1

    def change_mesh_mode(self):
        cur_indx = self.MESH_MODES.index(self.curr_mode)
        self.curr_mode = self.MESH_MODES[(cur_indx + 1) % len(self.MESH_MODES)]
        if hasattr(self, 'mesh'):
            self.mesh.mode = self.curr_mode

    def on_touch_down(self, touch):
        if hasattr(self, 'mesh'):
            if self.collide_point(*touch.pos):
                # The touch has occurred inside the widgets area.
                # Zoom in and out functionality
                if touch.is_mouse_scrolling:
                    prev_scale = list(self.scale.xyz)
                    if touch.button == 'scrolldown':
                        new_scale = [sc_ax + self.zoom_speed for sc_ax in prev_scale]
                    elif touch.button == 'scrollup':
                        new_scale = [sc_ax - self.zoom_speed for sc_ax in prev_scale]
                    self.scale.xyz = tuple(new_scale)

                # Accumulators for rotation
                self.Dx, self.Dy = 0, 0
                self.store_quat = self.quat
                touch.grab(self)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if hasattr(self, 'mesh'):
                self.Dx -= touch.dx
                self.Dy += touch.dy

                new_quat = euler_to_quaternion([0.01 * self.Dx, 0.01 * self.Dy, 0])
                self.quat = quat_mult(self.store_quat, new_quat)

                euler_radians = quaternion_to_euler(self.quat)
                self.roll.angle, self.pitch.angle, self.yaw.angle = euler_to_roll_pitch_yaw(euler_radians)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
