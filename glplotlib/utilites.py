import numpy as np


def reshape_vertex_map(points):
    """
    If points is a image-shaped point cloud, reshape to simple array of points.
    :param points: (H, W, 3) or (N, 3) shape of numpy array
    :return: (H*W, 3) or (N, 3) shape of nunmpy array
    """
    if len(points.shape) == 3:
        points = points.reshape((points.shape[0] * points.shape[1], points.shape[2]))
    return points


def normalize_colors(colors):
    """
    If colors are integer 8bit values, scale to 0 to 1 float value used by opengl
    :param colors:
    :return:
    """
    if colors.dtype is not np.float32:
        colors = colors.astype(np.float32) / 255.0
    return colors
