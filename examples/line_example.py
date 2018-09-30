import time
import numpy as np
from glplotlib import GPVisualizer
import pyqtgraph as pg

vis = GPVisualizer()


def fn(x, y):
    return np.cos((x ** 2 + y ** 2) ** 0.5)


def add_grid(vis):
    gx = vis.add_grid_generic()
    gx.rotate(90, 0, 1, 0)
    gx.translate(-10, 0, 0)
    gy = vis.add_grid_generic()
    gy.rotate(90, 1, 0, 0)
    gy.translate(0, -10, 0)
    gz = vis.add_grid_generic()
    gz.translate(0, 0, -10)


def add_lines(vis):
    n = 51
    y = np.linspace(-10, 10, n)
    x = np.linspace(-10, 10, 100)
    for i in range(n):
        yi = np.array([y[i]] * 100)
        d = (x ** 2 + yi ** 2) ** 0.5
        z = 10 * np.cos(d) / (d + 1)
        pts = np.vstack([x, yi, z]).transpose()
        vis.add_line_generic(pos=pts, color=pg.glColor((i, n * 1.3)), width=(i + 1) / 10., antialias=True)


def main():
    vis.show()
    add_grid(vis)
    add_lines(vis)
    time.sleep(30)


if __name__ == '__main__':
    main()
