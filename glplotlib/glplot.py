from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np
import threading

from glplotlib import utilites


class GPGLViewWidget(gl.GLViewWidget, QtCore.QObject):
    """
    A class derived from gl.GLViewWidget.

    Extended with QObject with multiple signals and slots. Expected to be run in a separate thread.
    """
    exit_signal = QtCore.pyqtSignal()
    clear_signal = QtCore.pyqtSignal()
    add_item_delegate_signal = QtCore.pyqtSignal(object, object)
    method_delegate_signal = QtCore.pyqtSignal(object, object)
    function_delegate_signal = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None):
        """
        Same as GLViewWidget.
        :param parent: parent of this Qt Object.
        """
        super(GPGLViewWidget, self).__init__(parent=parent)
        self.execute_event_lock = threading.Lock()
        self.execute_event = threading.Event()
        self.execute_result = None
        self.real_close = False

        self.clear_signal.connect(self.clear_slot)
        self.add_item_delegate_signal.connect(self.add_item_delegate_slot)
        self.method_delegate_signal.connect(self.method_delegate_slot)
        self.exit_signal.connect(self.exit_slot)
        self.function_delegate_signal.connect(self.function_delegate_slot)

    def closeEvent(self, event):
        """
        Overrides the existing behavior of closing a view window.

        Now, closing window does not terminates the app.
        :param event: close event
        :return: None
        """
        if not self.real_close:
            event.ignore()
            self.hide()
        else:
            super(GPGLViewWidget, self).closeEvent(event)

    @QtCore.pyqtSlot()
    def clear_slot(self):
        """
        Handle to remove all items in current widget.
        :return:
        """
        self.items = []
        self.update()

    @QtCore.pyqtSlot(object, object)
    def add_item_delegate_slot(self, func, params):
        """
        Handle to delegate creating pyqtgraph.opengl items.

        The created item can be manipulated in the main thread.
        :param func: class/constructor of a pyqtgraph.opengl items
        :param params: parameters passed to __init__ of the pyqtgraph.opengl items,
        can be either dict or iterable.
        :return:
        """
        try:
            item = None
            if type(params) is dict:
                item = func(**params)
            else:
                iterator = iter(params)
                item = func(*iterator)
            self.addItem(item)
            self.execute_result = item
        except Exception as error:
            self.execute_result = error
        self.execute_event.set()

    @QtCore.pyqtSlot(object, object)
    def method_delegate_slot(self, name, params):
        """
        Handle to delegate all method call to this widget.
        :param name: the method to be called in str.
        :param params: parameters passed to the method, can be either dict or iterable.
        :return:
        """
        try:
            method = getattr(self, name)
            if type(params) is dict:
                self.execute_result = method(**params)
            else:
                iterator = iter(params)
                self.execute_result = method(*iterator)
        except Exception as error:
            self.execute_result = error
        self.execute_event.set()

    @QtCore.pyqtSlot(object, object)
    def function_delegate_slot(self, func, params):
        """
        Handle to delegate all method call in the same thread as this widget.
        :param func: the function object to be called
        :param params: parameters passed to the function, can be either dict or iterable.
        :return:
        """
        try:
            if type(params) is dict:
                self.execute_result = func(**params)
            else:
                iterator = iter(params)
                self.execute_result = func(*iterator)
        except Exception as error:
            self.execute_result = error
        self.execute_event.set()

    @QtCore.pyqtSlot()
    def exit_slot(self):
        """
        Handle that closes the widget and event loop
        :return:
        """
        self.real_close = True
        self.close()

    def show_delegate(self, persistent=True):
        """
        Delegate method to external show function
        :param persistent:
        :return:
        """
        self.real_close = not persistent
        self.show()


class GPVisualizer(threading.Thread):
    """
    The object to launch GPGLViewWidget in a separate thread.

    At most one per process. Instance of this thread lives in global GLPLOT_VISUALIZER_INSTANCE.
    This Object should not created by ordinary user.
    """
    app = None
    widget = None
    running = threading.Event()

    def __init__(self):
        """
        Initializer that invokes the tread containing GPGLViewWidget.

        Does nothing if the thread is already created by other instance of this class.
        This initializer wait until QApplication and GPGLViewWidget are already created.
        """
        super(GPVisualizer, self).__init__()
        if not GPVisualizer.running.is_set():
            self.start()
            GPVisualizer.running.wait()

    def __del__(self):
        """
        Destructor. Shut down the Qt event loop if running.
        :return:
        """
        if GPVisualizer.running.is_set():
            self.clean_up()

    def run(self):
        """
        The procedure to be run in the separate thread.

        This function creates QApplication and GPGLViewWidget,
        sets the running event, and launches the Qt event loop.
        :return:
        """
        GPVisualizer.app = QtGui.QApplication([])
        GPVisualizer.widget = GPGLViewWidget()

        GPVisualizer.running.set()
        GPVisualizer.app.exec()
        GPVisualizer.running.clear()

    @classmethod
    def clean_up(cls):
        """
        Stops Qt event loop and cleans up resources.
        :return:
        """
        if cls.widget is not None:
            cls.widget.exit_signal.emit()
            cls.widget = None
        cls.app = None
        cls.running.clear()

    @classmethod
    def add_item_delegate(cls, func, params):
        """
        Creates a pyqtgraph.opengl item in the separate thread, and fetch a reference of the object.

        This function waits to startt until event loop is running,
        and uses execute_event lock/event pair to perform synchronization.
        The created item can be manipulated in the main thread.
        :param func: The class/initializer of the pyqtgraph.opengl item to be created.
        :param params: parameters passed to the initializer.
        :return: The created pyqtgraph.opengl item, can be manipulated in the main thread.
        """
        cls.running.wait()
        cls.widget.execute_event_lock.acquire()
        cls.widget.execute_event.clear()

        cls.widget.add_item_delegate_signal.emit(func, params)
        cls.widget.execute_event.wait()

        result = cls.widget.execute_result
        cls.widget.execute_result = None
        cls.widget.execute_event_lock.release()

        if type(result) is Exception:
            raise result
        return result

    @classmethod
    def method_delegate(cls, name, params=None):
        """
        Calls a method of GPGLViewWidget in the separate thread.

        :param name: the method to be called in str.
        :param params: parameters passed to the method, can be either dict or iterable.
        :return: the return value of the method ot be called.
        """
        cls.running.wait()
        cls.widget.execute_event_lock.acquire()
        cls.widget.execute_event.clear()

        if params is None:
            params = dict()

        cls.widget.method_delegate_signal.emit(name, params)
        cls.widget.execute_event.wait()

        result = cls.widget.execute_result
        cls.widget.execute_result = None
        cls.widget.execute_event_lock.release()

        if type(result) is Exception:
            raise result
        return result

    @classmethod
    def function_delegate(cls, func, params=None):
        """
        Calls a function in the same thread as GPGLViewWidget.

        :param func: the function object to be called
        :param params: parameters passed to the function, can be either dict or iterable.
        :return: the return value of the function
        """
        cls.running.wait()
        cls.widget.execute_event_lock.acquire()
        cls.widget.execute_event.clear()

        if params is None:
            params = dict()

        cls.widget.method_delegate_signal.emit(func, params)
        cls.widget.execute_event.wait()

        result = cls.widget.execute_result
        cls.widget.execute_result = None
        cls.widget.execute_event_lock.release()

        if type(result) is Exception:
            raise result
        return result

    @classmethod
    def clear(cls):
        """
        Removes all items in GPGLViewWidget.
        :return:
        """
        cls.running.wait()
        cls.widget.clear_signal.emit()

    @classmethod
    def get_widget(cls):
        """
        Get a reference of the widget, created in the separate thread.
        :return: a reference of the widget
        """
        return cls.widget


"""
The global variable that holds a instance of the only GPVisualizer.
"""
GLPLOT_VISUALIZER_INSTANCE = GPVisualizer()


def show(persistent=True):
    """
    Show the window of visualizer.
    :param persistent: If False, will terminate the event loop immediately after the window is closed.
    If True, the window and widget simply hides in the background.
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'persistent': persistent
    }
    vis.method_delegate('show_delegate', param)


def hide():
    """
    Hide the window of visualizer.
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.method_delegate('hide')


def close_app():
    """
    Shut down Qt event loop and clean up resources. Only to be called upon closing the application.
    :return:
    """
    global GLPLOT_VISUALIZER_INSTANCE
    GLPLOT_VISUALIZER_INSTANCE.clean_up()
    GLPLOT_VISUALIZER_INSTANCE = None


def is_alive():
    """
    Check if the visualizer and Qt event loop is running.
    :return: Bool of whether its running.
    """
    return GPVisualizer.running.is_set()


def update():
    """
    Update the content on the window and widget immediately.
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.method_delegate('update')


def get_widget():
    """
    Returns a reference to the GPGLViewWidget created in another thread.
    :return:
    """
    if GLPLOT_VISUALIZER_INSTANCE is not None:
        return GLPLOT_VISUALIZER_INSTANCE.get_widget()


def set_opts(**kwargs):
    """
    Set options of the GPGLViewWidget. For details of the options, check pyqtgraph.opengl.GLViewWidget.
    http://www.pyqtgraph.org/documentation/3dgraphics/glviewwidget.html
    http://www.pyqtgraph.org/documentation/_modules/pyqtgraph/opengl/GLViewWidget.html#GLViewWidget
    :param kwargs: keyword arguments of options to be set.
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.widget.opts.update(kwargs)
    update()


def set_title(title):
    """
    Set title of the window.
    :param title: str
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.method_delegate('setWindowTitle', [title])


def remove_item(item):
    """
    Remove the specific item held by GPGLViewWidget.
    :param item: a pyqtgraph.opengl item, already held by GPGLViewWidget
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'item': item
    }
    vis.method_delegate('removeItem', param)


def clear():
    """
    Remove all items in current widget.
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.clear()


def grid_generic(size=None, color=None, antialias=True, glOptions='translucent'):
    """
    Add a pyqtgraph.opengl.GLGridItem to GPGLViewWidget, with exactly the same arguments.

    For detail, consult documentation of pyqtgraph.opengl.GLGridItem:
    http://www.pyqtgraph.org/documentation/3dgraphics/glgriditem.html
    :param size: QVector3D. The size of the axes (in its local coordinate system; this does not affect the transform)
    :param color: QColor
    :param antialias: Bool
    :param glOptions: str
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'size': size,
        'color': color,
        'antialias': antialias,
        'glOptions': glOptions
    }
    item = vis.add_item_delegate(gl.GLGridItem, param)
    return item


def scatter_generic(pos, color=(1, 1, 1, 1), size=1.5, pxMode=True):
    """
    Add a pyqtgraph.opengl.GLScatterPlotItem to GPGLViewWidget, with exactly the same arguments.

    For detail, consult documentation of pyqtgraph.opengl.GLScatterPlotItem.
    http://www.pyqtgraph.org/documentation/3dgraphics/glscatterplotitem.html
    :param pos: (N,3) array of floats specifying point locations.
    :param color: (N,4) array of floats (0.0-1.0) specifying spot colors
    OR a tuple of floats specifying a single color for all spots.
    :param size: (N,) array of floats specifying spot sizes or a single value to apply to all spots.
    :param pxMode: If True, spot sizes are expressed in pixels. Otherwise, they are expressed in item coordinates.
    :return: pyqtgraph.opengl.GLScatterPlotItem, created in the same thread as GPGLViewWidget.
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'pos': pos,
        'color': color,
        'size': size,
        'pxMode': pxMode
    }
    item = vis.add_item_delegate(gl.GLScatterPlotItem, param)
    return item


def mesh_generic(meshdata,
                     faceColor=(1, 1, 1, 1),
                     edgeColor=(1, 1, 1, 1),
                     drawEdges=False,
                     drawFaces=True,
                     shader=None,
                     smooth=False,
                     computeNormals=True):
    """
    Add a pyqtgraph.opengl.GLMeshItem to GPGLViewWidget, with exactly the same arguments.

    For detail, consult documentation of pyqtgraph.opengl.GLMeshItem:
    http://www.pyqtgraph.org/documentation/3dgraphics/glmeshitem.html
    :param meshdata: pyqtgraph.opengl.MeshData object from which to determine geometry for this item.
    :param faceColor: Default face color used if no vertex or face colors are specified.
    :param edgeColor: Default edge color to use if no edge colors are specified in the mesh data.
    :param drawEdges: If True, a wireframe mesh will be drawn. (default=False)
    :param drawFaces: If True, mesh faces are drawn. (default=True)
    :param shader: Name of shader program to use when drawing faces. (None for no shader)
    :param smooth: If True, normal vectors are computed for each vertex and interpolated within each face.
    :param computeNormals: If False, then computation of normal vectors is disabled.
    This can provide a performance boost for meshes that do not make use of normals.
    :return: pyqtgraph.opengl.GLMeshItem, created in the same thread as GPGLViewWidget.
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'meshdata': meshdata,
        'color': faceColor,
        'edgeColor': edgeColor,
        'drawEdges': drawEdges,
        'drawFaces': drawFaces,
        'shader': shader,
        'smooth': smooth,
        'computeNormals': computeNormals
    }
    item = vis.add_item_delegate(gl.GLMeshItem, param)
    return item


def line_generic(pos, color=(1, 1, 1, 1), width=0.1, antialias=True, mode='line_strip'):
    """
     Add a pyqtgraph.opengl.GLLinePlotItem to GPGLViewWidget, with exactly the same arguments.

     For detail, consult documentation of pyqtgraph.opengl.GLLinePlotItem:
    http://www.pyqtgraph.org/documentation/3dgraphics/gllineplotitem.html
    :param pos: (N,3) array of floats specifying point locations.
    :param color: (N,4) array of floats (0.0-1.0)
    or tuple of floats specifying a single color for the entire item.
    :param width: float specifying line width
    :param antialias: enables smooth line drawing
    :param mode: ‘lines’: Each pair of vertexes draws a single line segment.
    or ‘line_strip’: All vertexes are drawn as a continuous set of line segments.
    :return: pyqtgraph.opengl.GLLinePlotItem, created in the same thread as GPGLViewWidget.
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'pos': pos,
        'color': color,
        'width': width,
        'antialias': antialias,
        'mode': mode
    }
    item = vis.add_item_delegate(gl.GLLinePlotItem, param)
    return item


def axis_generic(size=None, antialias=True, glOptions='translucent'):
    """
    Add a pyqtgraph.opengl.GLAxisItem to GPGLViewWidget, with exactly the same arguments.

    For detail, consult documentation of pyqtgraph.opengl.GLAxisItem:
    http://www.pyqtgraph.org/documentation/3dgraphics/glaxisitem.html
    :param size:
    :param antialias:
    :param glOptions:
    :return:
    """
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'size': size,
        'antialias': antialias,
        'glOptions': glOptions
    }
    item = vis.add_item_delegate(gl.GLAxisItem, param)
    return item


def point_cloud(pos, color=(1, 1, 1, 1), size=1.5, pxMode=True):
    """
    A helper function around scatter_generic to better deal with
    image shaped point cloud
    :param pos: (H, W, 3) or (N, 3) shape of numpy array, representing 3D points
    :param color: (H, W, 3) or (N, 3) shape of numpy array, representing RGB color
    :param size: (N,) array of floats specifying spot sizes or a single value to apply to all spots.
    :param pxMode: If True, spot sizes are expressed in pixels. Otherwise, they are expressed in item coordinates.
    :return: pyqtgraph.opengl.GLScatterPlotItem, created in the same thread as GPGLViewWidget.
    """
    if isinstance(pos, np.ndarray):
        pos = utilites.reshape_vertex_map(pos)
    if isinstance(color, np.ndarray):
        color = utilites.normalize_colors(color)
    item = scatter_generic(pos=pos, color=color, size=size, pxMode=pxMode)
    item.setGLOptions('opaque')
    return item


def update_point_cloud(item, pos=None, color=None):
    """
    Update data of a existing point_cloud object, can be used for animation.
    :param item: pyqtgraph.opengl.GLScatterPlotItem
    :param pos: (H, W, 3) or (N, 3) shape of numpy array, representing 3D points
    :param color: (H, W, 3) or (N, 3) shape of numpy array, representing RGB color
    :return:
    """
    if isinstance(pos, np.ndarray):
        pos = utilites.reshape_vertex_map(pos)
    if isinstance(color, np.ndarray):
        color = utilites.normalize_colors(color)
    if pos is not None and color is not None:
        item.setData(pos=pos, color=color)
    elif pos is not None:
        item.setData(pos=pos)
    elif color is not None:
        item.setData(color=color)


def edge_set(verts, edges, color=(1, 1, 1, 1), width=0.1):
    """
    A helper function for visualizing vertex-index list data structure
    :param verts: (N, 3) numpy array, representing 3D points
    :param edges: (E, 2) integer numpy array, each row represent index of two vertices of an edges
    :param color: (2*N, 4) array of floats (0.0-1.0)
    or tuple of floats specifying a single color for the entire item.
    :param width: float specifying line width
    :return: pyqtgraph.opengl.GLLinePlotItem, created in the same thread as GPGLViewWidget.
    """
    lines = np.empty((len(edges) * 2, 3), dtype=verts.dtype)
    lines[0::2] = verts[edges[:, 0]]
    lines[1::2] = verts[edges[:, 1]]

    item = line_generic(pos=lines, color=color, width=width, mode='line_strip')
    return item


def update_edge_set(item, verts, edges):
    """
    Update data of a existing edge_set object, can be used for animation
    :param item: pyqtgraph.opengl.GLLinePlotItem
    :param verts: (N, 3) numpy array, representing 3D points
    :param edges: (E, 2) integer numpy array, each row represent index of two vertices of an edges
    :return:
    """
    lines = np.empty((len(edges) * 2, 3), dtype=verts.dtype)
    lines[0::2] = verts[edges[:, 0]]
    lines[1::2] = verts[edges[:, 1]]
    item.setData(pos=lines)
