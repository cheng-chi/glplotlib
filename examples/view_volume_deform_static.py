from os.path import join
import numpy as np
import trimesh
from glplotlib.glplot import GPVisualizer, MeshData

vis = GPVisualizer()
vis.show()
dataset_root = '/home/chicheng/ARMLab/data/VolumeDeformData/hoodie'


def main():
    canonical_mesh_path = join(dataset_root, 'canonical', 'frame-000000.canonical.ply')
    mesh = trimesh.load(canonical_mesh_path)
    grid = vis.add_grid()
    scatter = vis.add_scatter(np.array(mesh.vertices), mesh.visual.vertex_colors.astype(np.float32) / 255.0, 1.5)
    scatter.setGLOptions('opaque')

    meshdata = MeshData(vertexes=mesh.vertices, faces=mesh.faces, faceColors=mesh.visual.face_colors.astype(np.float32) / 255.0)
    mesh_item = vis.add_mesh(meshdata)

