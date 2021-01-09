import numpy as np
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty
from kivy.resources import resource_find
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import glEnable, glDisable, GL_DEPTH_TEST
from kivy.graphics import RenderContext, Callback, PushMatrix, PopMatrix, \
    Color, Translate, Rotate, Mesh, UpdateNormalMatrix, Scale

from objloader import ObjFile


class MeshData(object):
    def __init__(self, vertices=None, faces=None, **kwargs):
        self.vertex_format = [
            (b'v_pos', 3, 'float'),
            (b'v_normal', 3, 'float'),
            (b'v_tc0', 2, 'float')]

        self.vertices = np.array(vertices)
        self.faces = np.array(faces)

        self.gl_verts = []
        self.indices = []

    def init_gl_verts(self):
        vert_norms, self.indices = self.extract_norms_and_indices(self.vertices, self.faces)
        self.verts_formatted = np.array([
                np.concatenate((vert, norm, [0, 0])) for vert, norm in zip(self.vertices, vert_norms)
            ])
        self.gl_verts = self.verts_formatted.flatten().tolist()

    def extract_norms_and_indices(self, verts, faces):
        """ Extract the vertex normals and indices

        Parameters
        ----------
        verts : array_like (N x 3)
            The 3D coordinates of the N vertices of the object
        faces: array_like (F x 3)
            The F triangles described by the 3 vertices' indices

        Returns
        -------
        vert_norms: array_like (N x 3)
            The normals calculated for each vertex
        indices: list
            The indices of the vertices that form triangles in a flat list, as specified by opengl
        """

        vert_norms = np.zeros(shape=(len(verts), 3))
        vert_count = np.zeros(len(verts)).astype('uint8')
        indices = []
        for tri in faces:
            verts_tri = verts[tri]
            face_norm = self.calc_face_norm(verts_tri)
            for vid in tri:
                vert_norms[vid] += face_norm
                vert_count[vid] += 1
                indices.append(vid)

        vert_norms /= np.resize(vert_count, (vert_count.shape[0], 3))
        return vert_norms, indices

    def calc_face_norm(self, tri):
        """ Calculates the surface normal for a triangle

        Parameters
        ----------
        tri : array_like (3 x 3)
            The 3D coordinates of the 3 vertices of the triangle

        Returns
        -------
        n : array_like (3, )
            The surface normal vector of the triangle
        """

        n = np.zeros(shape=(3))
        u = tri[1] - tri[0]
        v = tri[2] - tri[0]
        n[0] = u[1] * v[2] - u[2] * v[1]
        n[1] = u[2] * v[0] - u[0] * v[2]
        n[2] = u[0] * v[1] - u[1] * v[0]
        return n

    def update_verts(self, new_verts):
        if not hasattr(self, 'verts_formatted'):
            return

        for i in range(self.verts_formatted.shape[0]):
            self.verts_formatted[i][:3] = new_verts[i]
        self.gl_verts = self.verts_formatted.flatten().tolist()


class Renderer(Widget):

    MESH_MODES = ('points', 'line_strip', 'line_loop', 'lines', 'triangles', 'triangle_strip', 'triangle_fan')
    curr_mode = StringProperty('')
    nframes = NumericProperty(-1)

    def __init__(self, smpl_faces_path=None, frame_label=None, mode_label=None, **kwargs):

        self.frame_label = frame_label
        self.mode_label = mode_label
        self.smpl_faces = np.load(smpl_faces_path)

        # Make a canvas and add simple view
        self.canvas = RenderContext(compute_normal_mat=True)
        self.canvas.shader.source = resource_find('simple.glsl')
        super(Renderer, self).__init__(**kwargs)

        self.scene = ObjFile(resource_find("monkey.obj"))

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

    def on_curr_mode(self, *args):
        self.mode_label.text = f'Current mesh mode: {self.curr_mode}'

    def on_nframes(self, *args):
        self.frame_label.text = f'Frame count: {self.nframes}'

    def setup_scene(self, object):
        self.curr_obj = object
        with self.canvas:
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            Color(0, 0, 0, 1)
            PushMatrix()
            self.trans = Translate(0, 0, -3)
            self.roty = Rotate(1, 0, 1, 0)
            self.rotx = Rotate(1, 1, 0, 0)
            self.scale = Scale(1, 1, 1)
            UpdateNormalMatrix()
            if object in self.create_mesh_fn.keys():
                self.create_mesh_fn[object]()
            PopMatrix()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)

        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-asp, asp, -1, 1, 0.8, 100, 1)
        self.canvas['projection_mat'] = proj
        self.canvas['diffuse_light'] = (1.0, 1.0, 0.8)
        self.canvas['ambient_light'] = (0.1, 0.1, 0.1)

    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def reset_scene(self):
        self.canvas.clear()
        self.reset_timers(('scale', 'rotate', 'deform'))

        if hasattr(self, 'mesh'):
            del(self.mesh)

        self.nframes = 0

    def reset_timers(self, timer_spec):
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
        self.mesh_data = MeshData(vertices=m.verts_raw, faces=m.faces)
        self.mesh_data.gl_verts = m.vertices
        self.mesh_data.indices = m.indices

    def create_monkey_mesh_no_norms(self):
        m = list(self.scene.objects.values())[0]
        self.mesh_data = MeshData(vertices=m.verts_raw, faces=m.faces)
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

        self.mesh_data = MeshData(vertices=verts, faces=self.smpl_faces.tolist())
        self.mesh_data.init_gl_verts()
        self.mesh = Mesh(
            vertices=self.mesh_data.gl_verts,
            indices=self.mesh_data.indices,
            fmt=self.mesh_data.vertex_format,
            mode=self.curr_mode
        )

    def create_smpl_mesh(self):
        verts = np.random.rand(6890, 3) * 2 - 1
        self.mesh_data = MeshData(vertices=verts, faces=self.smpl_faces.tolist())
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
        self.mesh_data = MeshData()
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
            self.reset_timers((anim,))
            if play:
                self.timers[anim] = Clock.schedule_interval(self.animations[anim], 1/60.)

    def scale_anim(self, delta):
        step = ((self.nframes) % 360) * np.pi / 180.
        scale_factors = (np.sin(step) * 0.7 + 0.9, -np.sin(step) * 0.7 + 0.9, 1)
        self.scale.xyz = scale_factors
        self.nframes += 1

    def rotate_anim(self, delta):
        self.roty.angle += delta * 50
        self.nframes += 1

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

    def set_keypoints(self, new_kpnts):
        self.mesh.points = new_kpnts.flatten().tolist()
        self.nframes += 1

    def change_mesh_mode(self):
        cur_indx = self.MESH_MODES.index(self.curr_mode)
        self.curr_mode = self.MESH_MODES[(cur_indx + 1) % len(self.MESH_MODES)]
        if hasattr(self, 'mesh'):
            self.mesh.mode = self.curr_mode

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # The touch has occurred inside the widgets area. Do stuff!
            touch.grab(self)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if hasattr(self, 'mesh'):
                self.roty.angle += touch.dx
                self.rotx.angle -= touch.dy

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
