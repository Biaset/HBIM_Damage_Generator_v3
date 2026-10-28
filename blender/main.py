"""Create tessellated square damage meshes in Blender and write them to IFC.

Run with Blender 4.5.x, with the IFC/Bonsai add-on and IfcOpenShell available.
"""
from pathlib import Path
import sys
import pandas as pd
import ifcopenshell
import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
ENRICHED_POINTS_CSV = OUTPUT_DIR / "enriched_point_cloud.csv"
FILTERED_CLUSTERS_CSV = OUTPUT_DIR / "filtered_cluster_attributes.csv"
INPUT_IFC = OUTPUT_DIR / "UMINHO_monastery_Junqueria_with_ifc_damages_2.ifc"
OUTPUT_IFC = OUTPUT_DIR / "updated_4.ifc"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from damage_generator import IfcQuery, pset_epoch_id
from damage_modeling_points_projection import create_point_cluster_as_squares
from ifc_obj_merging import push_blender_patches_to_ifc


def main():
    enriched_points = pd.read_csv(ENRICHED_POINTS_CSV)
    filtered_clusters = pd.read_csv(FILTERED_CLUSTERS_CSV)
    model = ifcopenshell.open(str(INPUT_IFC))

    # Remove previously generated damage meshes to avoid duplicate Blender objects on reruns.
    for obj in list(bpy.data.objects):
        if obj.get("damage_guid") is not None:
            bpy.data.objects.remove(obj, do_unlink=True)

    cluster_lookup = filtered_clusters.set_index("cluster_id", drop=False)
    for cluster_id in filtered_clusters["cluster_id"].dropna().unique():
        if cluster_id not in cluster_lookup.index:
            continue
        cluster_points = enriched_points[enriched_points["cluster_id"] == cluster_id]
        if cluster_points.empty:
            print(f"[WARNING] No points found for cluster_id={cluster_id}; skipped.")
            continue
        row = cluster_lookup.loc[cluster_id]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        damage_guid = row.get("damage_id")
        host_guid = row.get("host_id")
        damage_type = row.get("damage_type", "Unknown")
        epoch = row.get("timestamp", cluster_points.iloc[0].get("Timestamp", ""))
        if pd.isna(damage_guid) or pd.isna(host_guid):
            print(f"[WARNING] Missing damage_id/host_id for cluster_id={cluster_id}; skipped.")
            continue
        # Preserve the original square size: size=0.01 is a 0.02 m (20 mm) side length.
        create_point_cluster_as_squares(
            name=f"Damage_{cluster_id}", points=cluster_points,
            damage_guid=str(damage_guid), host_guid=str(host_guid),
            damage_type=str(damage_type), epoch=str(epoch),
            r=float(row["Rf"]), g=float(row["Gf"]), b=float(row["Bf"]), size=0.01,
        )

    timestamps = filtered_clusters["timestamp"].dropna().astype(str).unique().tolist()
    timestamp = timestamps[0] if timestamps else ""
    push_blender_patches_to_ifc(model, timestamp)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.write(str(OUTPUT_IFC))
    print(f"Saved IFC model: {OUTPUT_IFC}")


if __name__ == "__main__":
    main()
