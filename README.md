# HBIM Damage Detection and Tessellated Damage Representation

This repository combines the point-cloud preprocessing/IFC enrichment workflow with the Blender stage used to represent detected damage in an IFC model. The original square-based representation is retained; the convex-hull workflow is not used by the Blender entry point.

## Workflow

1. Put the source point-cloud CSV in `data/input/point_cloud_classified.csv` and the source IFC model at the path expected by the first notebook cell (default: `data/input/UMINHO_monastery_Junqueria_2.ifc`).
2. Open `notebooks/main.ipynb` and run the preprocessing, host assignment, clustering, and IFC-damage preparation cells in order. Update the input/output paths and skip only the explicitly optional inspection/example cells.
3. Open `notebooks/filter_clusters.ipynb` to apply the original cluster-size filter and export `filtered_cluster_attributes.csv` to `data/output/`.
4. Open the Blender project containing the IFC host elements in **Blender 4.5.x**. Run `blender/main.py` from Blender's Python environment (or configure it as a script in Blender). The script reads `enriched_point_cloud.csv` and `filtered_cluster_attributes.csv` from `data/output/` and writes `updated_4.ifc` there.

## Requirements

- Python packages listed in `requirements.txt` for notebook processing.
- Blender **4.5.x** with the relevant IFC/Bonsai integration and compatible IfcOpenShell for the final stage.
- Input point-cloud CSV and IFC/BIM files (not included in the repository).

Local IFC/CSV/Blend files and generated outputs are excluded from version control by `.gitignore`. Review paths and timestamp formats in the notebooks before running; the notebook source is retained from the original project, with outputs removed and the project-root paths changed to the repository's `data/` folders.
