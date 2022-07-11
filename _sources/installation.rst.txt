Installation
#############

Honeybees runs on Python 3.9+ and requires the following packages to be installed. An example for Anaconda is given below, assuming you are in the Honeybees folder:

.. code-block::

    conda create --name <ENVNAME> python==3.9
    conda activate <ENVNAME>
    conda install netcdf4 pandas openpyxl geopandas numpy numba tbb tornado python-dateutil rasterio pyyaml matplotlib pillow
    pip install .

Required
**********
.. include:: ../requirements/requirements.txt
    :literal:

Tests
**********
.. include:: ../requirements/tests.txt
    :literal:

Documentation
**************
.. include:: ../requirements/docs.txt
    :literal: