import glplotlib.glplot as plt


def test():
    vis = GPVisualizer()
    vis.show()
    item = vis.add_grid_generic()
    # item = vis.add_scatter_generic(np.eye(3))
    # vis.remove_item(item)
    # result = vis.add_pcloud(np.eye(3), (1,1,1,1), 1)

    vis1 = GPVisualizer()
    vis1.show()
    vis1.add_grid_generic()

# test()