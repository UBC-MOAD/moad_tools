.. Copyright 2018 – present The UBC EOAS MOAD Group
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    https://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

.. SPDX-License-Identifier: Apache-2.0


************************
:py:obj:`moad_tools` API
************************

:py:mod:`moad_tools.geo_tools` Module
=====================================

.. automodule:: moad_tools.geo_tools
    :members:
    :undoc-members:
    :show-inheritance:


:py:mod:`moad_tools.observations` Module
========================================

.. automodule:: moad_tools.observations
    :members:
    :undoc-members:
    :show-inheritance:


:py:mod:`moad_tools.places` Module
==================================

.. automodule:: moad_tools.places
    :members:
    :undoc-members:
    :show-inheritance:


:py:mod:`moad_tools.midoss` Sub-package
=======================================

.. note::
    Modules in the :py:mod:`moad_tools.midoss` namespace require the installation of some
    packages that are not included the the ``moad-tools`` environment.
    To use any of the modules below or their command-line tools,
    please create and activate a ``moad-tools-midoss`` environment with:

        ``conda env create -f envs/environment-midoss.yaml``

        ``conda activate moad-tools-midoss``


.. _geotiff_watermaskModule:

:py:mod:`moad_tools.midoss.geotiff_watermask` Module
----------------------------------------------------

.. automodule:: moad_tools.midoss.geotiff_watermask
    :members:
    :undoc-members:
    :show-inheritance:


.. _geotiff-watermaskScript:

:command:`geotiff-watermask` Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :command:`geotiff-watermask` script calculates and stores a Numpy array file
containing a SalishSeaCast domain water mask for the AIS ship track density GeoTIFF files
used to generate oil spill parameters for Monte Carlo runs of MOHID.

Information about the :command:`geotiff-watermask` command-line arguments and options is available via:

.. code-block:: bash

    geotiff-watermask --help

.. code-block:: text

    Usage: geotiff-watermask [OPTIONS] GEOTIFF_FILE MESHMASK_FILE NUMPY_FILE

      Calculate and store a Numpy array file containing a SalishSeaCast domain
      water mask for the AIS ship track density GeoTIFF files used to generate oil
      spill parameters for Monte Carlo runs of MOHID.

      Please see

      https://ubc-moad-tools.readthedocs.io/en/latest/moad_tools.html#module-moad_tools.midoss.geotiff_watermask

      for more information about arguments and options.

    Options:
      --version                       Show the version and exit.
      -v, --verbosity [debug|info|warning|error|critical]
                                      Choose how much information you want to see
                                      about the progress of the calculation;
                                      warning, error, and critical should be
                                      silent unless something bad goes wrong.
                                      [default: warning]
      --help                          Show this message and exit.


:py:mod:`moad_tools.midoss.hdf5_to_netCDF4` Module
--------------------------------------------------

.. automodule:: moad_tools.midoss.hdf5_to_netcdf4
    :members:
    :undoc-members:
    :show-inheritance:


.. _hdf5-to-netcdf4Script:

:command:`hdf5-to-netcdf4` Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :command:`hdf5-to-netcdf4` script transforms selected contents of a MOHID HDF5 results
file into a netCDF4 file.

Information about the :command:`hdf5-to-netcdf4` command-line arguments and options is available via:

.. code-block:: bash

    hdf5-to-netcdf4 --help

.. code-block:: text

    Usage: hdf5-to-netcdf4 [OPTIONS] HDF5_FILE NETCDF4_FILE

      Transform selected contents of a MOHID HDF5 results file HDF5_FILE into a
      netCDF4 file stored as NETCDF4_FILE.

    Options:
      --version                       Show the version and exit.
      -v, --verbosity [debug|info|warning|error|critical]
                                      Choose how much information you want to see
                                      about the progress of the transformation;
                                      warning, error, and critical should be
                                      silent unless something bad goes wrong.
                                      [default: warning]
      --help                          Show this message and exit.


.. _RandomOilSpillsScript:

:command:`random-oil-spills` Script
-----------------------------------

The :command:`random-oil-spills` script produces a CSV file of randomly selected oil spill parameters.
Such a file is one of the items required to launch a collection of MOHID runs via the :ref:`mohidcmd:monte-carlo-sub-command` of the `MOHID command processor`_.

.. _MOHID command processor: https://mohid-cmd.readthedocs.io/en/latest/

Information about the :command:`random-oil-spills` command-line arguments and options is available via:

.. code-block:: bash

    random-oil-spills --help

.. code-block:: text

    Usage: random-oil-spills [OPTIONS] N_SPILLS CONFIG_FILE CSV_FILE

      Calculate and store a CSV file containing parameters of a set of random
      oil spills to drive Monte Carlo runs of MOHID.

      Please see

      https://ubc-moad-tools.readthedocs.io/en/latest/moad_tools.html#moad_tools.midoss.random_oil_spills.cli

      for more information about arguments and options, and

      https://ubc-moad-tools.readthedocs.io/en/latest/moad_tools.html#processing-configuration-yaml-file

      for details of the contents of the config file.

    Options:
      --version                       Show the version and exit.
      -v, --verbosity [debug|info|warning|error|critical]
                                      Choose how much information you want to see
                                      about the progress of the calculation;
                                      warning, error, and critical should be
                                      silent unless something bad goes wrong.
                                      [default: warning]

      --help                          Show this message and exit.


The :ref:`RandomOilSpillsFunctionsAndCommand-lineInterface` section below provides API details for the public functions that make up the :command:`random-oil-spills` script.


.. _RandomOilSpillsYAMLFile:

Processing Configuration YAML File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A collection of values for the processing that the :command:`random-oil-spills` performs
are stored in a YAML file that is passed in as the command-line argument ``CONFIG_FILE``.

In contrast to the :command:`random-oil-spills` command-line arguments ``N_SPILLS`` and
``CSV_FILE`` that may be different every time the script is run,
the values in the YAML file are likely to change only rarely.
Storing them in a
(version controlled)
YAML file avoids the tedium of typing them for every invocation of :command:`random-oil-spills`.

Here is an example YAML file:

.. code-block:: yaml

    # Config items for random-oil-spills script

    # Starting and ending dates of period from which
    # spill dates and hours are to be selected
    start date: 2015-01-01
    end date: 2018-12-31

    # Directory path to read AIS GeoTIFF files from
    geotiffs dir: /media/doug/warehouse/MIDOSS/ShipTrackDensityGeoTIFFs/

    # Directory path to read AIS vessel track shapefiles from
    shapefiles dir: /media/doug/warehouse/MIDOSS/ShipTrackShapefiles/

    # File to read SalishSeaCast NEMO domain water mask for AIS GeoTIFF files from
    geotiff watermask: /media/doug/warehouse/MIDOSS/ShipTrackDensityGeoTIFFs/geotiff-watermask.npy

    # File to read SalishSeaCast NEMO mesh mask from
    nemo meshmask: /media/doug/warehouse/MEOPAR/grid/mesh_mask201702.nc

    # List of vessel types
    vessel types:
      - tanker
      - atb
      - barge
      - cargo
      - cruise
      - ferry
      - fishing
      - smallpass
      - other

    # File to read oil attribution data from
    oil attribution: /media/doug/warehouse/MIDOSS/marine_transport_data/oil_attribution.yaml


.. _RandomOilSpillsFunctionsAndCommand-lineInterface:

Functions and Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: moad_tools.midoss.random_oil_spills
    :members:
    :undoc-members:
    :show-inheritance:
