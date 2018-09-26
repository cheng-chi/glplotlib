"""
A lightweight high-performance 3D visualizer based on pyqtgraph
"""

from setuptools import setup

setup(
    name='glplotlib',
    version='0.1.0',
    packages=['glplotlib'],
    include_package_data=True,
    install_requires=[
        "numpy",
        "pyopengl",
        "pyqt5==5.10.1",
        "pyqtgraph"
    ]
)
