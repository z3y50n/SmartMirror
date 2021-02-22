import numpy as np


def calc_face_norm(tri):
    """ Calculate the surface normal for a triangle

    Parameters
    ----------
    tri : array_like (3 x 3)
        The 3D coordinates of the 3 vertices of the triangle

    Returns
    -------
    n : array_like (3)
        The surface normal vector of the triangle
    """

    n = np.zeros(shape=(3))
    u = tri[1] - tri[0]
    v = tri[2] - tri[0]
    n[0] = u[1] * v[2] - u[2] * v[1]
    n[1] = u[2] * v[0] - u[0] * v[2]
    n[2] = u[0] * v[1] - u[1] * v[0]
    return n


def extract_norms_and_indices(verts, faces):
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
        The indices of the vertices of successive triangles in a flat list, required by opengl
    """

    vert_norms = np.zeros(shape=(verts.shape[0], 3))
    indices = []
    for tri in faces:
        tri_verts = verts[tri]
        face_norm = calc_face_norm(tri_verts)
        for vid in tri:
            vert_norms[vid] += face_norm
            indices.append(vid)

    return vert_norms, indices


class GLMeshData(object):
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
    verts_gl: list
        The openGL buffer that holds the vertices' data
    """
    vertex_format = [
        (b'v_pos', 3, 'float'),
        (b'v_normal', 3, 'float'),
        (b'v_tc0', 2, 'float')
    ]

    def __init__(self, vertices=None, faces=None, normals=None, **kwargs):
        self.verts_formatted = np.empty(shape=(vertices.shape[0], 8))
        if faces is not None:
            self.faces = np.array(faces)
            self.populate_normals_and_indices(vertices)
        if normals is not None:
            self.normals = normals

        self.texture_coords = np.zeros(shape=(vertices.shape[0], 2))
        self.vertices = vertices

    def populate_normals_and_indices(self, vertices):
        self.normals, self.indices = extract_norms_and_indices(vertices, self.faces)

    @property
    def vertices(self):
        return self._vertices

    @vertices.setter
    def vertices(self, verts):
        if self.verts_formatted.shape[0] != verts.shape[0]:
            return (False, 'The number of vertices does not correspond to this mesh')
        self._vertices = verts
        for i in range(self.verts_formatted.shape[0]):
            self.verts_formatted[i][:3] = self._vertices[i]
        self.verts_formatted = self.verts_formatted

    @property
    def normals(self):
        return self._normals

    @normals.setter
    def normals(self, norms):
        if self.verts_formatted.shape[0] != norms.shape[0]:
            return (False, 'The number of normals is not equal to the number of vertices')
        self._normals = norms
        for i in range(self.verts_formatted.shape[0]):
            self.verts_formatted[i][3:6] = self._normals[i]

    @property
    def texture_coords(self):
        return self._texture_coords

    @texture_coords.setter
    def texture_coords(self, text):
        if self.verts_formatted.shape[0] != text.shape[0]:
            return (False, 'The number of texture coordinates is not equal to the number of vertices')
        self._texture_coords = text
        for i in range(self.verts_formatted.shape[0]):
            self.verts_formatted[i][6:] = self._texture_coords[i]

    @property
    def verts_formatted(self):
        return self._verts_formatted

    @verts_formatted.setter
    def verts_formatted(self, verts_formatted):
        self._verts_formatted = verts_formatted
        self.verts_gl = self._verts_formatted.flatten().tolist()


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
