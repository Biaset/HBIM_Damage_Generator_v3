from datetime import datetime

import bmesh
import bpy
import ifcopenshell.api as api

from damage_generator import pset_epoch_id

def get_mesh_data_from_blender_object(obj):
    mesh = obj.data

    vertices = []
    for v in mesh.vertices:
        co_world = obj.matrix_world @ v.co
        vertices.append([float(co_world.x), float(co_world.y), float(co_world.z)])

    faces = []
    for poly in mesh.polygons:
        if len(poly.vertices) == 3:
            faces.append([int(i) for i in poly.vertices])
        else:
            # triangulate non-triangular faces
            verts = list(poly.vertices)
            for i in range(1, len(verts) - 1):
                faces.append([verts[0], verts[i], verts[i + 1]])

    return vertices, faces

def write_mesh_to_ifc_product(model, product, vertices, faces, r=None, g=None, b=None):
    context = None
    subs = model.by_type("IfcGeometricRepresentationSubContext")
    for c in subs:
        if (c.ContextIdentifier or "").lower() == "body":
            context = c
            break
    if context is None:
        context = model.by_type("IfcGeometricRepresentationContext")[0]

    # IFC triangulated faces are 1-based
    faces_1based = [[a + 1, b + 1, c + 1] for a, b, c in faces]

    cpl = model.create_entity(
        "IfcCartesianPointList3D",
        CoordList=vertices
    )

    tfs = model.create_entity(
        "IfcTriangulatedFaceSet",
        Coordinates=cpl,
        CoordIndex=faces_1based,
        Closed=False
    )

    shape = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="Tessellation",
        Items=[tfs]
    )

    # --- IFC color style ---
    if r is not None:
            style = api.run(
                "style.add_style",
                model,
                name=f"DamageStyle_{product.GlobalId}"
            )

            api.run(
                "style.add_surface_style",
                model,
                style=style,
                ifc_class="IfcSurfaceStyleShading",
                attributes={
                    "SurfaceColour": {
                        "Name": None,
                        "Red": float(r),
                        "Green": float(g),
                        "Blue": float(b),
                    }
                }
            )

            api.run(
                "style.assign_representation_styles",
                model,
                shape_representation=shape,
                styles=[style],
            )
        # -------------------------
    
    pdef = model.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape]
    )

    product.Representation = pdef


def get_pset_by_name(product, pset_name):
    for rel in product.IsDefinedBy or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pset = rel.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet") and pset.Name == pset_name:
                return pset
    return None

def compute_mesh_area(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    area = sum(face.calc_area() for face in bm.faces)
    bm.free()
    return area

def get_pset_by_name(product, pset_name):
    for rel in product.IsDefinedBy or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pset = rel.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet") and pset.Name == pset_name:
                return pset
    return None


def get_prop_by_name(pset, prop_name):
    for p in pset.HasProperties or []:
        if p.Name == prop_name:
            return p
    return None


def make_ifc_value(model, value):
    if isinstance(value, bool):
        return model.create_entity("IfcBoolean", value)
    elif isinstance(value, int):
        return model.create_entity("IfcInteger", value)
    elif isinstance(value, float):
        return model.create_entity("IfcReal", value)
    else:
        return model.create_entity("IfcText", str(value))


def add_or_update_single_value(model, pset, prop_name, value):
    prop = get_prop_by_name(pset, prop_name)
    nominal = make_ifc_value(model, value)

    if prop:
        prop.NominalValue = nominal
    else:
        new_prop = model.create_entity(
            "IfcPropertySingleValue",
            Name=prop_name,
            Description=None,
            NominalValue=nominal,
            Unit=None
        )
        props = list(pset.HasProperties or [])
        props.append(new_prop)
        pset.HasProperties = props


def push_blender_patches_to_ifc(model, datetime):

    for obj in bpy.data.objects:

        if "damage_guid" not in obj:
            continue

        damage_guid = obj["damage_guid"]

        damage_ifc = model.by_guid(damage_guid)

        if damage_ifc is None:
            print("Missing IFC object:", damage_guid)
            continue

        vertices, faces = get_mesh_data_from_blender_object(obj)

        r, g, b = obj["Rf"], obj["Gf"], obj["Bf"]

        coverage_area = round(compute_mesh_area(obj), 3)
        pset_name = pset_epoch_id(datetime)

        pset = get_pset_by_name(damage_ifc, pset_name)

        # api.run(
        #     "pset.edit_pset",
        #     model,
        #     pset=pset,
        #     properties={
        #         "CoverageArea_PTUM": float(coverage_area),
        #         #"SeverityLevel_PTUM": severity
        #     })

        if pset is not None:
            add_or_update_single_value(model, pset, "CoverageArea_PTUM", float(coverage_area))
        
        write_mesh_to_ifc_product(model, damage_ifc, vertices, faces, r, g, b)

        print("Updated IFC damage:", damage_guid)