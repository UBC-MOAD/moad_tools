.. Copyright 2018-2020 The UBC EOAS MOAD Group
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

*********************
:kbd:`moad_tools` API
*********************

:kbd:`moad_tools.geo_tools` Module
==================================

.. automodule:: moad_tools.geo_tools
    :members:
    :undoc-members:
    :show-inheritance:


:kbd:`moad_tools.observations` Module
=====================================

.. automodule:: moad_tools.observations
    :members:
    :undoc-members:
    :show-inheritance:


:kbd:`moad_tools.places` Module
===============================

.. automodule:: moad_tools.places
    :members:
    :undoc-members:
    :show-inheritance:


:kbd:`moad_tools.midoss` Sub-package
====================================

:command:`hdf5-to-netCDF4` Tool
-------------------------------

.. automodule:: moad_tools.midoss.hdf5_to_netcdf4
    :members:
    :undoc-members:
    :show-inheritance:


:command:`random-oil-spills` Script
-----------------------------------

.. _RandomOilSpillsYAMLFile:

Processing Configuration YAML File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A collction of values for the processing that the :command:`random-oil-spills` performs are stored in a YAML file that is passed in as the command-line argument :kbd:`CONFIG_FILE`.

In contrast to the :command:`random-oil-spills` command-line arguments :kbd:`N_SPILLS` and :kbd:`CSV_FILE` that may be different every time the script is run,
the values in the YAML file are likely to change only rarely.
Storing them in a
(version controlled)
YAML file aviods the tedium of typing them for every invocation of :command:`random-oil-spills`.

Here is an example YAML file:

.. code-block:: yaml

    # Config items for random-oil-spills script

    # Starting and ending dates of period from which
    # spill dates and hours are to be selected
    start date: 2015-01-01
    end date: 2018-12-31

    # Directory path to read AIS GeoTIFF files from
    geotiffs dir: /media/doug/warehouse/MIDOSS/ShipTrackDensityGeoTIFFs/


Functions and Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: moad_tools.midoss.random_oil_spills
    :members:
    :undoc-members:
    :show-inheritance:
