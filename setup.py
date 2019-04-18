from setuptools import setup

DESCRIPTION = """
GLPlotLib is a thin wrapper around PyQtGraph with Matplotlib style API.

GLPlotLib launches 3D OpenGL visualizations of PyQtGraph in a separate thread, allowing 
it to be used in a interactive python shell, without blocking the main thread.
"""


setupOpts = dict(
    name='glplotlib',
    description='a thin wrapper around PyQtGraph with Matplotlib style API',
    long_description=DESCRIPTION,
    license='MIT',
    url='https://github.com/chichengumich/glplotlib',
    author='Cheng Chi',
    author_email='chicheng@umich.edu',
)


setup(
    version='0.1.0',
    packages=['glplotlib'],
    include_package_data=True,
    install_requires=[
        "numpy",
        "pyopengl",
        "pyqt5==5.10.1",
        "pyqtgraph"
    ],
    **setupOpts
)
