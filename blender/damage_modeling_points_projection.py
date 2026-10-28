import numpy as np
import bpy

def create_point_cluster_as_squares(
    name, points, damage_guid, host_guid, damage_type, epoch, r, g, b, size=0.01
):
    verts = []
    faces = []

    pts = points[["X", "Y", "Z"]].to_numpy()

    for p in pts:
        i = len(verts)
        x, y, z = p

        verts.extend([
            [x - size, y - size, z],
            [x + size, y - size, z],
            [x + size, y + size, z],
            [x - size, y + size, z],
        ])

        faces.append([i, i + 1, i + 2, i + 3])

    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj["damage_guid"] = damage_guid
    obj["host_guid"] = host_guid
    obj["damage_type"] = damage_type
    obj["epoch"] = epoch
    obj["Rf"] = float(r)
    obj["Gf"] = float(g)
    obj["Bf"] = float(b)

    mat = bpy.data.materials.new(f"MAT_{name}")
    mat.diffuse_color = (float(r), float(g), float(b), 1.0)
    obj.data.materials.append(mat)
    obj.color = (float(r), float(g), float(b), 1.0)

    return obj

# def create_point_cluster_object(name, points, damage_guid, host_guid, damage_type, epoch, r, g, b):
#     import bpy

#     mesh = bpy.data.meshes.new(name + "_mesh")
#     obj = bpy.data.objects.new(name, mesh)
#     bpy.context.collection.objects.link(obj)

#     vertices = points[["X", "Y", "Z"]].to_numpy().tolist()

#     # no faces, no edges
#     mesh.from_pydata(vertices, [], [])
#     mesh.update()

#     obj["damage_guid"] = damage_guid
#     obj["host_guid"] = host_guid
#     obj["damage_type"] = damage_type
#     obj["epoch"] = epoch
#     obj["Rf"] = float(r)
#     obj["Gf"] = float(g)
#     obj["Bf"] = float(b)

#     mat = bpy.data.materials.new(f"MAT_{name}")
#     mat.diffuse_color = (r, g, b, 1.0)
#     obj.data.materials.append(mat)

#     obj.color = (float(r), float(g), float(b), 1.0)


#     return obj



