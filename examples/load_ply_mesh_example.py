import sys
import time
import numpy as np
import trimesh
import glplotlib.glplot as plt
from glplotlib import MeshData


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
    plt.grid_generic()
    plt.mesh_generic(meshdata)
    plt.show(persistent=False)
    # time.sleep(30)
    # plt.close_app()


if __name__ == '__main__':
    main()
