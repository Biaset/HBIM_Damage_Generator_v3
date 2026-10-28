import numpy as np
import ifcopenshell.geom
def verts_faces_to_ifc(verts, faces_idx):
    verts = np.asarray(verts)
    faces_arr = np.asarray(faces_idx)

    vertices_list = [[float(x), float(y), float(z)] for x, y, z in verts]

    faces_list = []
    for f in faces_arr:
        # ensure length-3 face
        if len(f) != 3:
            raise ValueError("Faces must be triangles (length 3). Got: %r" % (f,))
        # convert to ints
        tri = [int(f[0]), int(f[1]), int(f[2])]
        faces_list.append(tri)
    return vertices_list, faces_list

def wall_mesh_vertices(ifc_wall, settings=None):
    """
    Returns Nx3 numpy array of wall mesh vertices in WORLD coordinates.
    """
    if settings is None:
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)  # important!
        # optional:
        # settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)

    shape = ifcopenshell.geom.create_shape(settings, ifc_wall)
    verts = np.array(shape.geometry.verts, dtype=float).reshape((-1, 3))
    return verts


def wall_face_plane_from_placement(wall, wall_verts, plc):
    """
    Returns two planes (p_min, n) and (p_max, n) where n is the wall side normal,
    and p_min/p_max are points lying on the two opposite side faces.
    """

    M = np.array(plc.get_local_placement(wall.ObjectPlacement), dtype=float)  # 4x4
    origin = M[:3, 3]
    x = M[:3, 0]  # local X in world
    x = x / np.linalg.norm(x)
    z = M[:3, 2]  # local Z in world
    z = M[:3, 2]
    z = z / np.linalg.norm(z)

    y = np.cross(z, x)  # local Y (normal)
    y = y / np.linalg.norm(y)

    # signed distances of wall vertices along y, relative to origin
    d = (wall_verts - origin) @ y
    dmin, dmax = float(d.min()), float(d.max())

    p_min = origin + y * dmin
    p_max = origin + y * dmax
    return (p_min, y), (p_max, y)

def closest_wall_face_plane_to_patch(V_patch, planeA, planeB):
    """
    planeA, planeB: (p, n) with n unit
    Returns the plane (p, n) closer to the patch vertices V_patch.
    """
    pA, nA = planeA
    pB, nB = planeB

    # signed distances
    dA = (V_patch - pA) @ nA
    dB = (V_patch - pB) @ nB

    # use mean absolute distance as "closeness" score
    scoreA = np.mean(np.abs(dA))
    scoreB = np.mean(np.abs(dB))

    return planeA, nA if scoreA <= scoreB else planeB, nB

def project_points_to_plane(V, plane_point, plane_normal, offset=-0.005):
    """
    V: (N,3) vertices
    plane_point: (3,)
    plane_normal: (3,) unit normal
    offset: meters along normal (positive = away from surface)
    """
    # n = plane_normal / np.linalg.norm(plane_normal)
    n = plane_normal
    # signed distance from plane
    d = (V - plane_point) @ n
    V_proj = V - np.outer(d, n)
    return V_proj + offset * n