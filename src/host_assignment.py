import ifcopenshell.geom
import numpy as np
from rtree import index
from scipy.spatial import cKDTree

# p = index.Property()
# p.dimension = 3
# idx = index.Index(properties=p)

class DamageHostAssignment:
    def __init__(self, settings, model, idx, host_elements):
        #self.element = element
        self.settings = settings
        self.model = model
        self.idx = idx
        self.host_elements = host_elements
        self.elements = None
        self.element_kd = None

    def element_bounding_box(self, element):
        shape = ifcopenshell.geom.create_shape(self.settings, element)
        verts = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3)
        vert_min = verts.min(axis=0)
        vert_max = verts.max(axis=0)
        return vert_min, vert_max, verts

    def elements_bounding_box_tolerance(self):
        self.elements = []
        eid = 0

        for el in self.host_elements:
            try:
                vert_min, vert_max, _ = self.element_bounding_box(el)
            except Exception:
                continue
            tolerance = 1  # 5cm
            bounding_box = (
            vert_min[0] - tolerance, vert_min[1] - tolerance, vert_min[2] - tolerance, vert_max[0] + tolerance,
            vert_max[1] + tolerance, vert_max[2] + tolerance)
            self.idx.insert(eid, bounding_box)
            self.elements.append(el)
            eid += 1


    def kdt_for_elements(self):
        self.element_kd = {}

        for element in self.elements:
            vert_min, vert_max, verts = self.element_bounding_box(element)
            self.element_kd[element.GlobalId] = cKDTree(verts)

    def assign_host(self, points_xyz, points_n=None, max_distance=1, max_angle_deg=30):
        #cos_thr = np.cos(np.deg2rad(max_angle_deg))
        out_host = np.empty(len(points_xyz), dtype=object)

        for i, point in enumerate(points_xyz):
            candidate_element_ids = list(self.idx.intersection((point[0], point[1], point[2], point[0], point[1], point[2])))
            best = (np.inf, None)

            for candidate_id in candidate_element_ids:
                element = self.elements[candidate_id]
                tree = self.element_kd[element.GlobalId]
                distance, _ = tree.query(point, k=1)

                if distance < best[0] and distance <= max_distance:
                    best = (distance, element.GlobalId)

            out_host[i] = best[1]
        return out_host
