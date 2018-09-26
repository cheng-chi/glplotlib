from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np
import threading
import uuid


class GPGLViewWidget(gl.GLViewWidget, QtCore.QObject):
    exit_signal = QtCore.pyqtSignal()

    show_signal = QtCore.pyqtSignal()
    remove_item_signal = QtCore.pyqtSignal(object)
    clear_signal = QtCore.pyqtSignal()
    add_item_delegate_signal = QtCore.pyqtSignal(object, object)
    remove_item_delegate_signal = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(GPGLViewWidget, self).__init__(parent=parent)
        self.plot_items = dict()
        self.execute_event_lock = threading.Lock()
        self.execute_event = threading.Event()
        self.execute_result = None

        self.show_signal.connect(self.show_slot)
        self.remove_item_signal.connect(self.remove_item_slot)
        self.clear_signal.connect(self.clear_slot)
        self.add_item_delegate_signal.connect(self.add_item_delegate_slot)
        self.remove_item_delegate_signal.connect(self.remove_item_delegate_slot)

        self.exit_signal.connect(self.kill)
        self.real_close = False

    def closeEvent(self, event):
        print('close clicked!')
        print(event)
        if not self.real_close:
            event.ignore()
            self.hide()
        else:
            super(GPGLViewWidget, self).closeEvent(event)

    @QtCore.pyqtSlot()
    def show_slot(self):
        self.show()

    @QtCore.pyqtSlot(object)
    def remove_item_slot(self, item_id):
        item = self.plot_items[item_id]
        self.removeItem(item)

    @QtCore.pyqtSlot()
    def clear_slot(self):
        self.items = []
        self.update()

    @QtCore.pyqtSlot(object, object)
    def add_item_delegate_slot(self, func, params):
        item = func(**params)
        self.addItem(item)
        self.execute_result = item
        self.execute_event.set()

    @QtCore.pyqtSlot(object)
    def remove_item_delegate_slot(self, item):
        self.removeItem(item)
        self.execute_event.set()

    @QtCore.pyqtSlot()
    def kill(self):
        print('kill')
        self.real_close = True
        self.close()

    @QtCore.pyqtSlot(str)
    def print(self, text):
        print(text)
        self.show()

    @QtCore.pyqtSlot(object, object, object, object)
    def add_pcloud(self, item_id, pcloud, color, size):
        print(pcloud)
        pos = pcloud
        if len(pcloud.shape) == 3:
            pos = pcloud.reshape((pcloud.shape[0] * pcloud.shape[1], pcloud.shape[2]))
        sp = gl.GLScatterPlotItem(pos=pos, size=size, color=color, pxMode=True)
        sp.setGLOptions('opaque')
        self.addItem(sp)
        self.plot_items[item_id] = sp


class GPVisualizer(threading.Thread):
    app = None

    def __init__(self):
        super(GPVisualizer, self).__init__()
        self.running = threading.Event()
        self.start()
        self.running.wait()

    def run(self):
        if GPVisualizer.app is None:
            GPVisualizer.app = QtGui.QApplication([])

        self.widget = GPGLViewWidget()
        self.widget.opts['distance'] = 20
        self.widget.setWindowTitle('default')

        self.running.set()
        self.app.exec()
        self.running.clear()
        GPVisualizer.app.exit()
        GPVisualizer.app = None
        print('app_exited')

    def show(self):
        self.running.wait()
        self.widget.show_signal.emit()

    def remove_item(self, item_id):
        self.widget.remove_item_signal.emit(item_id)

    def clear(self):
        self.widget.clear_signal.emit()

    def add_gird(self, size=None, color=None, antialias=True, glOptions='translucent'):
        self.widget.execute_event_lock.acquire()
        self.widget.execute_event.clear()

        item_id = uuid.uuid4().hex
        self.widget.add_grid_signal.emit(item_id, size, color, antialias, glOptions)

        self.widget.execute_event.wait()
        self.widget.execute_event_lock.release()
        return item_id

    def add_point_cloud(self, pcloud, color, size):
        item_id = uuid.uuid4().hex
        self.widget.add_pcloud_signal.emit(item_id, pcloud, color, size)
        return item_id

    def add_item_delegate(self, func, params):
        self.widget.execute_event_lock.acquire()
        self.widget.execute_event.clear()

        self.widget.add_item_delegate_signal.emit(func, params)
        self.widget.execute_event.wait()

        result = self.widget.execute_result
        self.widget.execute_result = None
        self.widget.execute_event_lock.release()
        return result

    def remove_item_delegate(self, item):
        self.widget.execute_event_lock.acquire()
        self.widget.execute_event.clear()

        self.widget.remove_item_delegate_signal.emit(item)
        self.widget.execute_event.wait()

        self.widget.execute_event_lock.release()


def test():
    vis = GPVisualizer()
    # vis.add_gird()
    param = dict()
    item = vis.add_item_delegate(gl.GLGridItem, param)
    vis.show()
    vis.remove_item_delegate(item)
    # result = vis.add_pcloud(np.eye(3), (1,1,1,1), 1)