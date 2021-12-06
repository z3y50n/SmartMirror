import os
import math
from functools import partial
import numpy as np
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty
from kivy.resources import resource_find
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import glEnable, glDisable, GL_DEPTH_TEST
from kivy.graphics import (
    RenderContext,
    Callback,
    PushMatrix,
    PopMatrix,
    Translate,
    Rotate,
    Mesh,
    UpdateNormalMatrix,
    Scale,
)

from .play.mesh_utils import ObjFile, GLMeshData
from .utils.quaternion import (
    quaternion_to_euler,
    euler_to_quaternion,
    quat_mult,
    euler_to_roll_pitch_yaw,
)


MESH_MODES = (
    "points",
    "line_strip",
    "line_loop",
    "lines",
    "triangles",
    "triangle_strip",
    "triangle_fan",
)


class Renderer(Widget):

    _curr_mode = StringProperty("")
    _nframes = NumericProperty(-1)
    _zoom_speed = 0.03

    def __init__(self, smpl_faces_path=None, keypoints_spec=None, obj_mesh_path=None):

        if smpl_faces_path is not None:
            self._smpl_faces = np.load(smpl_faces_path)

        if keypoints_spec is not None:
            self.keypoints_spec = keypoints_spec.copy()
            self.keypoints_spec.sort(key=lambda kpnt: kpnt["smpl_indx"])
            # Extract the parent indices from the keypoints dictionary
            self.parents = [
                next(
                    (
                        indx
                        for (indx, kpnt) in enumerate(self.keypoints_spec)
                        if kpnt["name"] == p_kpnt["parent"]
                    ),
                    -1,
                )
                for p_kpnt in self.keypoints_spec
            ]

        if obj_mesh_path is not None:
            self._monkey_scene = ObjFile(obj_mesh_path)

        # Make a canvas and add simple view
        self.canvas = RenderContext(compute_normal_mat=True)

        shader_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "simple.glsl"
        )
        self._init_shader(shader_path)
        super().__init__()

        self._create_mesh_fn = {
            "monkey": self._create_monkey_mesh,
            "monkey_no_norms": self._create_monkey_mesh_no_norms,
            "random": self._create_rand_mesh,
            "smpl_mesh": self._create_smpl_mesh,
            "smpl_kpnts": self._create_smpl_kpnts,
            "error_vectors": self._create_error_vectors,
        }

        self._curr_mode = "triangles"
        self.curr_obj = None
        self._nframes = 0
        self.reset_scene()
        self._store_quat = None
        self._dx_acc, self._dy_acc = 0, 0

    def _init_shader(self, path):
        self.canvas.shader.source = resource_find(path)
        self.canvas["ambient_light"] = (0.2, 0.1, 0.2)

        self.reset_highlight()

    def setup_scene(self, rendered_obj, opts: dict = {}):
        self.curr_obj = rendered_obj
        self._recalc_normals = True
        self._update_glsl()
        with self.canvas:
            self.cb = Callback(self._setup_gl_context)
            PushMatrix()
            self.trans = Translate(0, 0, -3)
            self.rotx = Rotate(
                1, 1, 0, 0
            )  # so that the object does not break continuity
            self.scale = Scale(1, 1, 1)

            self.yaw = Rotate(0, 0, 0, 1)
            self.pitch = Rotate(0, -1, 0, 0)
            self.roll = Rotate(0, 0, 1, 0)
            self.quat = euler_to_quaternion([0, 0, 0])

            UpdateNormalMatrix()
            if rendered_obj in self._create_mesh_fn.keys():
                self._create_mesh_fn[rendered_obj](**opts)
            # self.trans.x += 1  # move everything to the right
            PopMatrix()
            self.cb = Callback(self._reset_gl_context)

    def _update_glsl(self):
        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-asp, asp, -1, 1, 1.5, 100, 1)
        self.canvas["projection_mat"] = proj

    def _setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)

    def _reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

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
            mode=self._curr_mode,
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
            mode=self._curr_mode,
        )

    def _create_smpl_mesh(self):
        verts = np.random.rand(6890, 3) * 2 - 1
        self._mesh_data = GLMeshData(vertices=verts, faces=self._smpl_faces)
        self._curr_mode = "triangles"
        self._mesh = Mesh(
            vertices=self._mesh_data.verts_gl,
            indices=self._mesh_data.indices,
            fmt=self._mesh_data.vertex_format,
            mode=self._curr_mode,
        )
        self.rotx.angle += 180

        # For debugging rotations: x,y,z axis
        # Mesh(
        #     vertices=[1, 0, 0, -1, -1, -1, 0, 0, 0, 0, 0, -1, -1, -1, 0, 0],
        #     indices=[0, 1],
        #     fmt=GLMeshData.vertex_format,
        #     mode='lines'
        # )
        # Mesh(
        #     vertices=[0, 1, 0, -1, -1, -1, 0, 0, 0, 0, 0, -1, -1, -1, 0, 0],
        #     indices=[0, 1],
        #     fmt=GLMeshData.vertex_format,
        #     mode='lines'
        # )
        # Mesh(
        #     vertices=[0, 0, 1, -1, -1, -1, 0, 0, 0, 0, 0, -1, -1, -1, 0, 0],
        #     indices=[0, 1],
        #     fmt=GLMeshData.vertex_format,
        #     mode='lines'
        # )

    def _create_smpl_kpnts(self):
        verts = np.random.rand(24, 3) * 2 - 1
        indices = []
        for indx, kpnt in enumerate(self.parents):
            if kpnt < 0:
                continue
            indices.extend([kpnt, indx])

        self._mesh_data = GLMeshData(verts, normals=-np.ones((24, 3)), indices=indices)
        self._curr_mode = "lines"
        self._mesh = Mesh(
            vertices=self._mesh_data.verts_gl,
            indices=self._mesh_data.indices,
            fmt=self._mesh_data.vertex_format,
            mode=self._curr_mode,
        )
        self.trans.z += 0.2
        self.rotx.angle += 180

    def _create_error_vectors(self, start_verts, direction_vecs):
        """Render lines starting at :param: `start_verts` and with direction :param: `direction_vecs`.

        Parameters
        ----------
        starts_verts: `numpy.array`, (N x 3)
            The starting points' 3D coordinates of the N lines
        direction_vecs: `numpy.array`, (N x 3)
            The direction vectors of the N error arrows
        """
        for i in range(start_verts.shape[0]):
            start_point = np.expand_dims(start_verts[i, :], axis=1).transpose()
            dir_vec = direction_vecs[i, :]
            self._create_arrow(start_point, dir_vec)

        self.rotx.angle += 180
        self.trans.z += 0.2

    def _create_arrow(self, start_point: np.array, dir_vec: np.array):
        """Renders an arrow starting from `start_point` and pointing towards `dir_vec`.

        Parameters
        ----------
        start_point : `numpy.array`, (3 x 1)
            The coordinates of the origin of the arrow.
        dir_vec : `numpy.array`, (3 x 1)
            The direction vector of the arrow.

        Returns
        -------
        arrow_shaft : `kivy.graphics.Mesh`
            The mesh data of the arrow's shaft.
        arrw_head : `kivy.graphics.Mesh`
            The mesh data of the arrow's head.
        """
        dir_vec /= 2
        end_point = start_point + dir_vec
        shaft_data = GLMeshData(
            np.concatenate((start_point, end_point), axis=0),
            normals=-np.ones((2, 3)),
            indices=[0, 1],
        )
        arrow_shaft = Mesh(
            vertices=shaft_data.verts_gl,
            indices=shaft_data.indices,
            fmt=shaft_data.vertex_format,
            mode="lines",
        )

        # Create the points of the arrow head's base circle
        bases = self._get_base_vecs(dir_vec)
        npoints = 20
        step = 2 * math.pi / npoints
        points = []
        for j in range(npoints):
            points.append(
                0.03 * (bases[0] * math.sin(step * j) + bases[1] * math.cos(step * j))
            )
        points = np.array(points)
        points += start_point + dir_vec * 0.8

        # Add to the points of the circle the tip of the arrow and set up the faces to create the mesh
        points = np.append(points, end_point, axis=0)
        faces = []
        for j in range(npoints):
            faces.append([j, npoints, (j + 1) % npoints])
        head_data = GLMeshData(points, faces=faces)
        arrow_head = Mesh(
            vertices=head_data.verts_gl,
            indices=head_data.indices,
            fmt=head_data.vertex_format,
            mode="triangles",
        )
        return (arrow_shaft, arrow_head)

    def _get_base_vecs(self, vec: np.array):
        """Create base 3 base vectors from a given vector.

        Parameters
        ----------
        vec : `numpy.array`, (3, )
            One vector of the resulting base vectors.

        Returns
        -------
        base1, base2 : `numpy.array`, (3, )
            The perpendicular vectors to the :param: `vec` and to each other. The three vectors `vec`, `base1`
            and `base2` form the base.
        """
        base1 = np.random.randn(3)
        base1 -= np.dot(vec, base1) * vec
        base1 /= np.linalg.norm(base1)
        base2 = np.cross(vec, base1)
        return base1, base2

    def set_vertices(self, vertices, keypoints):
        """Set the vertices of the currently rendered mesh.

        Parameters
        ----------
        vertices: `numpy.array`, (N x 3)
            The 3D coordinates of the mesh's N vertices.
        keypoints : `numpy.array`, (24 x 3)
            The 3D coordinates of the 24 SMPL keypoints.
        """
        if not hasattr(self, "_mesh"):
            return

        if self._recalc_normals and self.curr_obj == "smpl_mesh":
            self._mesh_data.populate_normals_and_indices(vertices)
            self._recalc_normals = False

        if self.curr_obj == "smpl_mesh":
            self._mesh_data.vertices = vertices
        elif self.curr_obj == "smpl_kpnts":
            self._mesh_data.vertices = keypoints

        self._curr_keypoints = keypoints
        self._highlight_keypoint()
        self._mesh.vertices = self._mesh_data.verts_gl
        self._nframes += 1

    def setup_highlight(self, kpnt_indx: int):
        """Setup the highlighting around the given keypoint.

        Parameters
        ----------
        kpnt_indx : `int`
            The SMPL index of the keypoint to highlight.
        """
        self._highlighted_kpnt_indx = kpnt_indx
        self.canvas["sphere_color"] = (0.415, 0.878, 0.662)
        self._highlight_keypoint()

    def _highlight_keypoint(self):
        """Highlight the selected keypoint for each frame."""
        if not hasattr(self, "_highlighted_kpnt_indx"):
            return

        sphere_center = self._curr_keypoints[self._highlighted_kpnt_indx]
        sphere_radius = (
            self.keypoints_spec[self._highlighted_kpnt_indx]["hradius"] * self.scale.x
        )

        self.canvas["sphere_center"] = tuple([float(coord) for coord in sphere_center])
        self.canvas["sphere_radius"] = float(sphere_radius)

    def reset_highlight(self):
        if not hasattr(self, "_highlighted_kpnt_indx"):
            return

        del self._highlighted_kpnt_indx
        self.canvas["sphere_color"] = (1.0, 1.0, 1.0)
        self.canvas["sphere_radius"] = 0.0

    def play_animation(self, animation_spec):
        if not hasattr(self, "_mesh"):
            raise UnboundLocalError("The mesh does not exist")

        if animation_spec == "correct_repetition":
            start_color = self.canvas["object_color"]
            target_color = (0.0, 0.6, 0.0)
            Clock.schedule_interval(
                partial(self._reach_color_anim, start_color, target_color, True), 0.01
            )

    def _reach_color_anim(self, start_color, target_color, reverse, dt):
        """Play a color animation on the rendered object. The animations starts from a starting color,
        reaches a target color and if :param: reverse is True, returns slowly back to the starting color.

        Parameters
        ----------
        start_color: tuple
            The rgb components specifying the starting color in the range [0,1].
        target_color: tuple
            The rgb components specifying the target color in the range [0, 1].
        reverse: bool
            If True, plays the animation in reverse when the target color is reached.
            If False, the animation ends when the target color is reached.
        """
        new_col = []
        for i in range(3):
            color_dif = target_color[i] - start_color[i]
            col_comp = self.canvas["object_color"][i] + color_dif * 0.05
            if (color_dif < 0 and col_comp < target_color[i]) or (
                color_dif > 0 and col_comp > target_color[i]
            ):
                col_comp = target_color[i]
            new_col.append(col_comp)

        self.canvas["object_color"] = tuple(new_col)
        if self.canvas["object_color"] == target_color:
            # When the target color is reached, play in reverse or stop the animation.
            if reverse:
                Clock.schedule_interval(
                    partial(self._reach_color_anim, target_color, start_color, False),
                    0.07,
                )
            return False

    def _scale_anim(self, delta):
        step = ((self._nframes) % 360) * np.pi / 180.0
        scale_factors = (np.sin(step) * 0.7 + 0.9, -np.sin(step) * 0.7 + 0.9, 1)
        self.scale.xyz = scale_factors

    def _rotate_anim(self, delta):
        self.roty.angle += delta * 50

    def _deform_anim(self, delta):
        vertices = (
            self._mesh_data.vertices
            + np.random.normal(size=self._mesh_data.vertices.shape) * 0.02
        )
        self.set_vertices(vertices)

    def change_mesh_mode(self):
        cur_indx = self._mesh_MODES.index(self._curr_mode)
        self._curr_mode = self._mesh_MODES[(cur_indx + 1) % len(self._mesh_MODES)]
        if hasattr(self, "_mesh"):
            self._mesh.mode = self._curr_mode

    def on_touch_down(self, touch):
        """Initialize potential rotation and handle scaling of the mesh."""
        if hasattr(self, "_mesh"):
            if self.collide_point(*touch.pos):
                # Zoom in and out functionality
                if touch.is_mouse_scrolling:
                    prev_scale = list(self.scale.xyz)
                    if touch.button == "scrolldown":
                        new_scale = [sc_ax + self._zoom_speed for sc_ax in prev_scale]
                    elif touch.button == "scrollup":
                        new_scale = [sc_ax - self._zoom_speed for sc_ax in prev_scale]
                    self.scale.xyz = tuple(new_scale)

                # Accumulators for rotation
                self._dx_acc, self._dy_acc = 0, 0
                self._store_quat = self.quat

                touch.grab(self)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """On mouse click and move, handle the rotation of the mesh."""
        if touch.grab_current is self:
            self._dx_acc += touch.dx
            self._dy_acc += touch.dy

            new_quat = euler_to_quaternion(
                [0.01 * self._dx_acc, 0.01 * self._dy_acc, 0]
            )
            self.quat = quat_mult(self._store_quat, new_quat)

            euler_radians = quaternion_to_euler(self.quat)
            self.roll.angle, self.pitch.angle, self.yaw.angle = euler_to_roll_pitch_yaw(
                euler_radians
            )
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        """If it was a single click, handle it."""
        if touch.grab_current is self:
            if touch.pos == touch.opos and not touch.is_mouse_scrolling:
                # If the position didnt change, this was a single click
                if hasattr(self, "single_click_handle"):
                    kpnts_2d = self._kpnts_to_2D()
                    closest_kpnts = self._find_closest_kpnts(touch.pos, kpnts_2d)
                    self.single_click_handle(touch.pos, closest_kpnts)
            touch.ungrab(self)
        return super().on_touch_down(touch)

    def _kpnts_to_2D(self):
        width, height = self.width, self.height
        verts_3d = self._curr_keypoints
        modelview = np.array(self.canvas["modelview_mat"].tolist())
        projection = np.array(self.canvas["projection_mat"].tolist())
        transforms_mat = self._get_transformation_matrix()

        verts_2d = np.zeros(shape=(verts_3d.shape[0], 2))
        for i, vert in enumerate(verts_3d):
            hom_vert = np.expand_dims(np.append(vert, 1), axis=1)
            pos = np.dot(modelview, hom_vert)
            pos = np.dot(projection, pos)
            pos = np.dot(transforms_mat, pos)
            pos[:3] /= pos[3]
            pos[0] = (pos[0] + 1) * width / 2.0
            pos[1] = (pos[1] + 1) * height / 2.0
            verts_2d[i, :] = pos[:2].flatten()
        return verts_2d

    def _get_transformation_matrix(self):
        scale = np.array(self.scale.matrix.tolist())
        rotx = np.array(self.rotx.matrix.tolist())
        roll = np.array(self.roll.matrix.tolist())
        pitch = np.array(self.pitch.matrix.tolist())
        yaw = np.array(self.yaw.matrix.tolist())
        transl = np.array(self.trans.matrix.tolist())

        mat = np.dot(transl, scale)
        mat = np.dot(roll, mat)
        mat = np.dot(pitch, mat)
        mat = np.dot(yaw, mat)
        mat = np.dot(rotx, mat)
        return mat

    def _find_closest_kpnts(self, pos, kpnts_2d):
        dists = np.linalg.norm(kpnts_2d - pos, axis=1)
        return self.keypoints_spec[dists.argmin()]["name"]
