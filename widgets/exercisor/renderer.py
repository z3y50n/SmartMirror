import os
from functools import partial
import numpy as np
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty
from kivy.resources import resource_find
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import glEnable, glDisable, GL_DEPTH_TEST
from kivy.graphics import RenderContext, Callback, PushMatrix, PopMatrix, \
    Translate, Rotate, Mesh, UpdateNormalMatrix, Scale

from play.mesh_utils import ObjFile, GLMeshData
from quaternion import quaternion_to_euler, euler_to_quaternion, quat_mult, euler_to_roll_pitch_yaw


class Renderer(Widget):

    MESH_MODES = ('points', 'line_strip', 'line_loop', 'lines', 'triangles', 'triangle_strip', 'triangle_fan')
    _curr_mode = StringProperty('')
    _nframes = NumericProperty(-1)
    _zoom_speed = 0.03

    def __init__(self, smpl_faces_path=None, obj_mesh_path=None):

        if smpl_faces_path is not None:
            self._smpl_faces = np.load(smpl_faces_path)

        if obj_mesh_path is not None:
            self._monkey_scene = ObjFile(obj_mesh_path)

        # Make a canvas and add simple view
        self.canvas = RenderContext(compute_normal_mat=True)

        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'simple.glsl')
        self.canvas.shader.source = resource_find(path)
        self.canvas['ambient_light'] = (0.2, 0.1, 0.2)
        super().__init__()

        self._create_mesh_fn = {
            'monkey': self._create_monkey_mesh,
            'monkey_no_norms': self._create_monkey_mesh_no_norms,
            'random': self._create_rand_mesh,
            'smpl_mesh': self._create_smpl_mesh,
            'smpl_kpnts': self._create_smpl_kpnts
        }

        self._curr_mode = 'triangles'
        self.curr_obj = None
        self._nframes = 0
        self.reset_scene()
        self._store_quat = None
        self._dx_acc, self._dy_acc = 0, 0

    def setup_scene(self, rendered_obj):
        self.curr_obj = rendered_obj
        self._recalc_normals = True
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
            if rendered_obj in self._create_mesh_fn.keys():
                self._create_mesh_fn[rendered_obj]()
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
        self._nframes = 0

    def _create_monkey_mesh(self):
        m = list(self._monkey_scene.objects.values())[0]
        self._mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            mode=self._curr_mode,
        )
        self._mesh_data = GLMeshData(vertices=np.array(m.verts_raw))
        self._mesh_data.verts_gl = m.vertices
        self._mesh_data.indices = m.indices

    def _create_monkey_mesh_no_norms(self):
        m = list(self._monkey_scene.objects.values())[0]
        self._mesh_data = GLMeshData(vertices=np.array(m.verts_raw), faces=m.faces)
        self._mesh = Mesh(
            vertices=self._mesh_data.verts_gl,
            indices=self._mesh_data.indices,
            fmt=self._mesh_data.vertex_format,
            mode=self._curr_mode
        )

    def _create_rand_mesh(self):
        verts = np.random.logistic(scale=0.5, size=(10000, 3))
        # verts = np.random.normal(scale=0.7, size=(10000, 3))
        # verts = np.random.laplace(scale=0.6, size=(10000, 3))
        # verts = np.random.lognormal(size=(10000, 3))

        self._mesh_data = GLMeshData(vertices=verts, faces=self._smpl_faces)
        self._mesh = Mesh(
            vertices=self._mesh_data.verts_gl,
            indices=self._mesh_data.indices,
            fmt=self._mesh_data.vertex_format,
            mode=self._curr_mode
        )

    def _create_smpl_mesh(self):
        verts = np.random.rand(6890, 3) * 2 - 1
        self._mesh_data = GLMeshData(vertices=verts, faces=self._smpl_faces)
        self._curr_mode = 'triangles'
        self._mesh = Mesh(
            vertices=self._mesh_data.verts_gl,
            indices=self._mesh_data.indices,
            fmt=self._mesh_data.vertex_format,
            mode=self._curr_mode
        )
        self.rotx.angle += 180

    def _create_smpl_kpnts(self):
        verts = np.random.rand(24, 3) * 2 - 1
        self._mesh_data = GLMeshData(verts)
        verts_formatted = np.concatenate((verts, -np.ones(shape=(24, 3)), np.zeros(shape=(24, 2))), axis=1)
        indices = []
        parents = [-1,  0,  0,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  9,  9, 12, 13, 14, 16, 17, 18, 19, 20, 21]
        for indx, kpnt in enumerate(parents):
            if kpnt < 0:
                continue
            indices.extend([kpnt, indx])

        self._mesh_data.verts_formatted = verts_formatted
        self._mesh_data.indices = indices
        self._mesh_data.verts_gl = verts_formatted.flatten().tolist()
        self._curr_mode = 'lines'
        self._mesh = Mesh(
            vertices=self._mesh_data.verts_gl,
            indices=self._mesh_data.indices,
            fmt=self._mesh_data.vertex_format,
            mode=self._curr_mode
        )
        self.rotx.angle += 180

    def set_vertices(self, vertices):
        if not hasattr(self, '_mesh'):
            return

        if self._recalc_normals and self.curr_obj == 'smpl_mesh':
            self._mesh_data.populate_normals_and_indices(vertices)
            self._recalc_normals = False

        self._mesh_data.vertices = vertices
        self._mesh.vertices = self._mesh_data.verts_gl
        self._nframes += 1

    def render_error_vectors(self, start_verts, vectors):
        target_verts = start_verts + vectors
        verts = np.concatenate((start_verts, target_verts), axis=0)
        verts_formatted = np.concatenate((verts, -np.ones((verts.shape[0], 3)), np.zeros((verts.shape[0], 3))), axis=1)
        for i in range(start_verts.shape[0]):
            pass
        with self.canvas:
            self.cb = Callback(self._setup_gl_context)
            PushMatrix()

            # error_mesh = Mesh(
            #     vertices=
            # )
            PopMatrix()
            self.cb = Callback(self._reset_gl_context)
        pass

    def play_animation(self, animation_spec):
        if not hasattr(self, '_mesh'):
            raise UnboundLocalError('The mesh does not exist')

        if animation_spec == 'correct_repetition':
            start_color = self.canvas['object_color']
            target_color = (0., 0.6, 0.)
            Clock.schedule_interval(partial(self._reach_color_anim, start_color, target_color, True), 0.01)

    def _reach_color_anim(self, start_color, target_color, reverse, dt):
        new_col = []
        for i in range(3):
            color_dif = target_color[i] - start_color[i]
            col_comp = self.canvas['object_color'][i] + color_dif * 0.05
            if (color_dif < 0 and col_comp < target_color[i]) \
               or (color_dif > 0 and col_comp > target_color[i]):
                col_comp = target_color[i]
            new_col.append(col_comp)

        self.canvas['object_color'] = tuple(new_col)
        if self.canvas['object_color'] == target_color:
            if reverse:
                Clock.schedule_interval(partial(self._reach_color_anim, target_color, start_color, False), 0.07)
            return False

    def _scale_anim(self, delta):
        step = ((self._nframes) % 360) * np.pi / 180.
        scale_factors = (np.sin(step) * 0.7 + 0.9, -np.sin(step) * 0.7 + 0.9, 1)
        self.scale.xyz = scale_factors

    def _rotate_anim(self, delta):
        self.roty.angle += delta * 50

    def _deform_anim(self, delta):
        vertices = self._mesh_data.vertices + np.random.normal(size=self._mesh_data.vertices.shape) * 0.02
        self.set_vertices(vertices)

    def change_mesh_mode(self):
        cur_indx = self._mesh_MODES.index(self._curr_mode)
        self._curr_mode = self._mesh_MODES[(cur_indx + 1) % len(self._mesh_MODES)]
        if hasattr(self, '_mesh'):
            self._mesh.mode = self._curr_mode

    def on_touch_down(self, touch):
        if hasattr(self, '_mesh'):
            if self.collide_point(*touch.pos):
                # The touch has occurred inside the widgets area.
                # Zoom in and out functionality
                if touch.is_mouse_scrolling:
                    prev_scale = list(self.scale.xyz)
                    if touch.button == 'scrolldown':
                        new_scale = [sc_ax + self._zoom_speed for sc_ax in prev_scale]
                    elif touch.button == 'scrollup':
                        new_scale = [sc_ax - self._zoom_speed for sc_ax in prev_scale]
                    self.scale.xyz = tuple(new_scale)

                # Accumulators for rotation
                self._dx_acc, self._dy_acc = 0, 0
                self._store_quat = self.quat
                touch.grab(self)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if hasattr(self, '_mesh'):
                self._dx_acc -= touch.dx
                self._dy_acc += touch.dy

                new_quat = euler_to_quaternion([0.01 * self._dx_acc, 0.01 * self._dy_acc, 0])
                self.quat = quat_mult(self._store_quat, new_quat)

                euler_radians = quaternion_to_euler(self.quat)
                self.roll.angle, self.pitch.angle, self.yaw.angle = euler_to_roll_pitch_yaw(euler_radians)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
        return super().on_touch_down(touch)
