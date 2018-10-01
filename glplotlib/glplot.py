from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np
import threading


class GPGLViewWidget(gl.GLViewWidget, QtCore.QObject):
    """
    A class derived from gl.GLViewWidget.

    Extended with QObject with multiple signals and slots. Expected to be run in a separate thread.
    """
    exit_signal = QtCore.pyqtSignal()
    clear_signal = QtCore.pyqtSignal()
    add_item_delegate_signal = QtCore.pyqtSignal(object, object)
    method_delegate_signal = QtCore.pyqtSignal(object, object)

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

    def closeEvent(self, event):
        """
        Overrides the existing behavior of closing a view window.

        Now, closing window does not terminates the app.
        :param event:
        :return:
        """
        if not self.real_close:
            event.ignore()
            self.hide()
        else:
            super(GPGLViewWidget, self).closeEvent(event)

    @QtCore.pyqtSlot()
    def clear_slot(self):
        self.items = []
        self.update()

    @QtCore.pyqtSlot(object, object)
    def add_item_delegate_slot(self, func, params):
        try:
            item = func(**params)
            self.addItem(item)
            self.execute_result = item
        except Exception as error:
            self.execute_result = error
        self.execute_event.set()

    @QtCore.pyqtSlot(object, object)
    def method_delegate_slot(self, name, params):
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

    @QtCore.pyqtSlot()
    def exit_slot(self):
        self.real_close = True
        self.close()

    def show_delegate(self, persistent=True):
        self.real_close = not persistent
        self.show()


class GPVisualizer(threading.Thread):
    app = None
    widget = None
    running = threading.Event()

    def __init__(self):
        super(GPVisualizer, self).__init__()
        if not GPVisualizer.running.is_set():
            self.start()
            GPVisualizer.running.wait()

    def __del__(self):
        if GPVisualizer.running.is_set():
            self.clean_up()

    def run(self):
        GPVisualizer.app = QtGui.QApplication([])

        GPVisualizer.widget = GPGLViewWidget()
        GPVisualizer.widget.opts['distance'] = 10
        GPVisualizer.widget.setWindowTitle('default title')

        GPVisualizer.running.set()
        GPVisualizer.app.exec()
        GPVisualizer.running.clear()

    @classmethod
    def clean_up(cls):
        if cls.widget is not None:
            cls.widget.exit_signal.emit()
            cls.widget = None
        cls.app = None
        cls.running.clear()

    @classmethod
    def add_item_delegate(cls, func, params):
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
    def clear(cls):
        cls.running.wait()
        cls.widget.clear_signal.emit()

    @classmethod
    def get_widget(cls):
        return cls.widget


GLPLOT_VISUALIZER_INSTANCE = GPVisualizer()


def show(persistent=True):
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'persistent': persistent
    }
    vis.method_delegate('show_delegate', param)


def hide():
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.method_delegate('hide')


def close_app():
    global GLPLOT_VISUALIZER_INSTANCE
    GLPLOT_VISUALIZER_INSTANCE.clean_up()
    GLPLOT_VISUALIZER_INSTANCE = None


def is_alive():
    return GPVisualizer.running.is_set()


def update():
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.method_delegate('update')


def set_opts(**kwargs):
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.widget.opts.update(kwargs)
    update()


def set_title(title):
    vis = GLPLOT_VISUALIZER_INSTANCE
    vis.method_delegate('setWindowTitle', [title])


def remove_item(item):
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'item': item
    }
    vis.method_delegate('removeItem', param)


def grid_generic(size=None, color=None, antialias=True, glOptions='translucent'):
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
    vis = GLPLOT_VISUALIZER_INSTANCE
    param = {
        'size': size,
        'antialias': antialias,
        'glOptions': glOptions
    }
    item = vis.add_item_delegate(gl.GLAxisItem, param)
    return item
