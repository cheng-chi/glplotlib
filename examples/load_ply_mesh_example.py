import sys
from os.path import join
import numpy as np
import trimesh
from glplotlib import GPVisualizer, MeshData

vis = GPVisualizer()


def load_mesh(path):
    mesh = trimesh.load(path)
    params = {
        'vertexes': mesh.vertices,
        'faces': mesh.faces,
        'faceColors': mesh.visual.face_colors.astype(np.float32) / 255.0
    }
    return params


def main():
    path = sys.argv[-1]
    print('Loading file: {}'.format(path))
    # path = u'/home/chicheng/ARMLab/data/VolumeDeformData/hoodie/canonical/frame-000000.canonical.ply'
    meshdata = MeshData(**load_mesh(path))
    vis.add_grid_generic()
    vis.add_mesh_generic(meshdata)
    vis.show()


if __name__ == '__main__':
    main()
