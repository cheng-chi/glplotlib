GLPlotLib
=========

GLPlotLib is a thin rapper around [PyQtGraph](https://github.com/pyqtgraph/pyqtgraph) with Matplotlib style API.

Copyright 2018 Cheng Chi, University of Michigan - Ann Arbor

GLPlotLib launches 3D OpenGL visualizations of PyQtGraph in a separate thread, allowing 
it to be used in a interactive python shell, without blocking the main thread.

Requirements
------------

  * PyQt5
  * python 3.x
  * NumPy
  * For 3D graphics: pyopengl
  * Known to run on Linux. It will NOT run on MacOS, due to its limitations.

Installation
-------------

`pip install glplotlib`
