import time
import numpy as np
from glplotlib import GPVisualizer

vis = GPVisualizer()


def generate_real_size_points():
    pos = np.empty((53, 3))
    size = np.empty((53,))
    color = np.empty((53, 4))
    pos[0] = (1, 0, 0)
    size[0] = 0.5
    color[0] = (1.0, 0.0, 0.0, 0.5)
    pos[1] = (0, 1, 0)
    size[1] = 0.2
    color[1] = (0.0, 0.0, 1.0, 0.5)
    pos[2] = (0, 0, 1)
    size[2] = 2. / 3.
    color[2] = (0.0, 1.0, 0.0, 0.5)

    z = 0.5
    d = 6.0
    for i in range(3, 53):
        pos[i] = (0, 0, z)
        size[i] = 2. / d
        color[i] = (0.0, 1.0, 0.0, 0.5)
        z *= 0.5
        d *= 2.0

    params = {
        'pos': pos,
        'size': size,
        'color': color,
        'pxMode': False
    }
    return params


def generate_animation(vis):
    pos = np.random.random(size=(100000, 3))
    pos *= [10, -10, 10]
    pos[0] = (0, 0, 0)
    color = np.ones((pos.shape[0], 4))
    d2 = (pos ** 2).sum(axis=1) ** 0.5
    size = np.random.random(size=pos.shape[0]) * 10
    phase = 0.

    pos3 = np.zeros((100, 100, 3))
    pos3[:, :, :2] = np.mgrid[:100, :100].transpose(1, 2, 0) * [-0.1, 0.1]
    pos3 = pos3.reshape(10000, 3)
    d3 = (pos3 ** 2).sum(axis=1) ** 0.5

    sp2 = vis.add_scatter_generic(pos=pos, color=(1,1,1,1), size=size)
    sp3 = vis.add_scatter_generic(pos=pos3, color=(1,1,1,.3), size=0.1, pxMode=False)

    for i in range(10000):
        ## update volume colors
        s = -np.cos(d2 * 2 + phase)
        color = np.empty((len(d2), 4), dtype=np.float32)
        color[:, 3] = np.clip(s * 0.1, 0, 1)
        color[:, 0] = np.clip(s * 3.0, 0, 1)
        color[:, 1] = np.clip(s * 1.0, 0, 1)
        color[:, 2] = np.clip(s ** 3, 0, 1)
        sp2.setData(color=color)
        phase -= 0.1

        ## update surface positions and colors
        z = -np.cos(d3 * 2 + phase)
        pos3[:, 2] = z
        color = np.empty((len(d3), 4), dtype=np.float32)
        color[:, 3] = 0.3
        color[:, 0] = np.clip(z * 3.0, 0, 1)
        color[:, 1] = np.clip(z * 1.0, 0, 1)
        color[:, 2] = np.clip(z ** 3, 0, 1)
        sp3.setData(pos=pos3, color=color)

        time.sleep(1.0/30)


def main():
    vis.add_grid_generic()
    vis.show()
    vis.add_scatter_generic(**generate_real_size_points())

    generate_animation(vis)


if __name__ == '__main__':
    main()