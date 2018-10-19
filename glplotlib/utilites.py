import numpy as np


def reshape_vertex_map(points):
    if len(points.shape) == 3:
        points = points.reshape((points.shape[0] * points.shape[1], points.shape[2]))
    return points


def normalize_colors(colors):
    if colors.dtype is not np.float32:
        colors = colors.astype(np.float32) / 255.0
    return colors
