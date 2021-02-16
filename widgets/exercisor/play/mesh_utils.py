import numpy as np


class CustomMeshData(object):
    """ Holds the data required to render a 3D mesh

    Attributes
    ----------
    vertex_format: list of tuples
        The format of the vertices' expected by the openGL buffer
    vertices: array_like (N x 3)
        The 3D coordinates of each of the N vertices of the mesh
    faces: array_like (F x 3)
        The 3 vertices' indices defining the F triangles
    indices: list
        The indices of the vertices that form triangles in a flat list, as specified by opengl
    verts_formatted: array_like (N x 8)
        The 3D coordinates, the normal vector and the 2D texture coordinates of the N vertices
    gl_verts: list
        The flatten openGL buffer that holds the vertices' data
    """
    __slots__ = ('vertex_format', 'vertices', 'faces', 'indices', 'verts_formatted', 'gl_verts')

    def __init__(self, vertices=None, faces=None, **kwargs):
        self.vertex_format = [
            (b'v_pos', 3, 'float'),
            (b'v_normal', 3, 'float'),
            (b'v_tc0', 2, 'float')]

        self.vertices = np.array(vertices)
        self.faces = np.array(faces)

        self.indices = []
        self.gl_verts = []

    def init_gl_verts(self):
        """ Construct the :attr: verts_formatted and the :attr: gl_verts
            using the :attr: vertices and the :attr: faces """
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
            The 3D coordinates of the N vertices of the mesh
        faces: array_like (F x 3)
            The 3 vertices' indices defining the F triangles

        Returns
        -------
        vert_norms: array_like (N x 3)
            The normals calculated for each vertex
        indices: list
            The indices of the vertices that form triangles in a flat list, as specified by opengl
        """

        vert_norms = np.zeros(shape=(len(verts), 3))
        indices = []
        for tri in faces:
            tri_verts = verts[tri]
            face_norm = self.calc_face_norm(tri_verts)
            for vid in tri:
                vert_norms[vid] += face_norm
                indices.append(vid)

        return vert_norms, indices

    def calc_face_norm(self, tri):
        """ Calculate the surface normal for a triangle

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
        """ Update the :attr: verts_formatted and the :attr: gl_verts

        Parameters
        ----------
        new_verts: array_like (N x 3)
            The 3D coordinates of the new vertices of the mesh
        """
        if not hasattr(self, 'verts_formatted'):
            return

        for i in range(self.verts_formatted.shape[0]):
            self.verts_formatted[i][:3] = new_verts[i]
        self.gl_verts = self.verts_formatted.flatten().tolist()


class MeshData(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.vertex_format = [
            (b'v_pos', 3, 'float'),
            (b'v_normal', 3, 'float'),
            (b'v_tc0', 2, 'float')]
        self.vertices = []
        self.indices = []
        self.verts_raw = []
        self.faces = []

    def calculate_normals(self):
        for i in range(len(self.indices) / (3)):
            fi = i * 3
            v1i = self.indices[fi]
            v2i = self.indices[fi + 1]
            v3i = self.indices[fi + 2]

            vs = self.vertices
            p1 = [vs[v1i + c] for c in range(3)]
            p2 = [vs[v2i + c] for c in range(3)]
            p3 = [vs[v3i + c] for c in range(3)]

            u, v = [0, 0, 0], [0, 0, 0]
            for j in range(3):
                v[j] = p2[j] - p1[j]
                u[j] = p3[j] - p1[j]

            n = [0, 0, 0]
            n[0] = u[1] * v[2] - u[2] * v[1]
            n[1] = u[2] * v[0] - u[0] * v[2]
            n[2] = u[0] * v[1] - u[1] * v[0]

            for k in range(3):
                self.vertices[v1i + 3 + k] = n[k]
                self.vertices[v2i + 3 + k] = n[k]
                self.vertices[v3i + 3 + k] = n[k]


class ObjFile:
    def finish_object(self):
        if self._current_object is None:
            return

        mesh = MeshData()
        mesh.verts_raw = self.vertices
        mesh.faces = [[f - 1 for f in fc[0]] for fc in self.faces]
        idx = 0
        for f in self.faces:
            verts = f[0]
            norms = f[1]
            tcs = f[2]
            for i in range(3):
                # get normal components
                n = (0.0, 0.0, 0.0)
                if norms[i] != -1:
                    n = self.normals[norms[i] - 1]

                # get texture coordinate components
                t = (0.0, 0.0)
                if tcs[i] != -1:
                    t = self.texcoords[tcs[i] - 1]

                # get vertex components
                v = self.vertices[verts[i] - 1]

                data = [v[0], v[1], v[2], n[0], n[1], n[2], t[0], t[1]]
                mesh.vertices.extend(data)

            tri = [idx, idx + 1, idx + 2]
            mesh.indices.extend(tri)
            idx += 3

        self.objects[self._current_object] = mesh
        # mesh.calculate_normals()
        self.faces = []

    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.objects = {}
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

        self._current_object = None

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'):
                continue
            if line.startswith('s'):
                continue
            values = line.split()
            if not values:
                continue
            if values[0] == 'o':
                self.finish_object()
                self._current_object = values[1]
            # elif values[0] == 'mtllib':
            #    self.mtl = MTL(values[1])
            # elif values[0] in ('usemtl', 'usemat'):
            #    material = values[1]
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(-1)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(-1)
                self.faces.append((face, norms, texcoords, material))
        self.finish_object()


def MTL(filename):
    contents = {}
    mtl = None
    return
    for line in open(filename, "r"):
        if line.startswith('#'):
            continue
        values = line.split()
        if not values:
            continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            raise ValueError("mtl file doesn't start with newmtl stmt")
        mtl[values[0]] = values[1:]
    return contents
