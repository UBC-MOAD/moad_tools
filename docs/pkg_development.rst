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


.. _moad_toolsPackagedDevelopment:

****************************************
:py:obj:`moad_tools` Package Development
****************************************

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&label=Python&logoColor=gold
    :target: https://docs.python.org/3.12/
    :alt: Python Version
.. image:: https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    :target: https://github.com/UBC-MOAD/moad_tools
    :alt: Git on GitHub
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter
.. image:: https://readthedocs.org/projects/ubc-moad-tools/badge/?version=latest
    :target: https://ubc-moad-tools.readthedocs.io/en/latest/
    :alt: Documentation Status
.. image:: https://github.com/UBC-MOAD/moad_tools/workflows/sphinx-linkcheck/badge.svg
    :target: https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Asphinx-linkcheck
    :alt: Sphinx linkcheck
.. image:: https://github.com/UBC-MOAD/moad_tools/workflows/pytest-with-coverage/badge.svg
    :target: https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Apytest-with-coverage
    :alt: Pytest with Coverage Status
.. image:: https://codecov.io/gh/UBC-MOAD/moad_tools/branch/main/graph/badge.svg
    :target: https://app.codecov.io/gh/UBC-MOAD/moad_tools
    :alt: Codecov Testing Coverage Report
.. image:: https://github.com/UBC-MOAD/moad_tools/actions/workflows/codeql-analysis.yaml/badge.svg
      :target: https://github.com/UBC-MOAD/moad_tools/actions?query=workflow:codeql-analysis
      :alt: CodeQL analysis
.. image:: https://img.shields.io/github/issues/UBC-MOAD/moad_tools?logo=github
    :target: https://github.com/UBC-MOAD/moad_tools/issues
    :alt: Issue Tracker

The UBC EOAS MOAD Group Tools package (:py:obj:`moad_tools`) is a collection of
Python modules that facilitate code reuse for the UBC EOAS MOAD Group.


.. _moad_toolsPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&label=Python&logoColor=gold
    :target: https://docs.python.org/3.12/
    :alt: Python Version

The :py:obj:`moad_tools` package is developed using `Python`_ 3.12.
It is tested for Python versions >=3.10.

.. _Python: https://www.python.org/


.. _moad_toolsGettingTheCode:

Getting the Code
================

.. image:: https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    :target: https://github.com/UBC-MOAD/moad_tools
    :alt: Git on GitHub

Clone the code and documentation `repository`_ from GitHub with:

.. _repository: https://github.com/UBC-MOAD/moad_tools

.. code-block:: bash

    $ git clone git@github.com:UBC-MOAD/moad_tools.git


.. _moad_toolsDevelopmentEnvironment:

Development Environment
=======================

Setting up an isolated development environment using `Conda`_ is recommended.
Assuming that you have `Miniconda3`_ installed,
you can create and activate an environment called ``moad-tools`` that will have
all of the Python packages necessary for development,
testing,
and building the documentation with the commands below:

.. _Conda: https://conda.io/en/latest/
.. _Miniconda3: https://docs.conda.io/en/latest/miniconda.html

.. code-block:: bash

    $ cd moad_tools
    $ conda env create -f envs/environment-dev.yaml
    $ conda activate moad-tools

:py:obj:`moad_tools` is installed in `editable install mode`_ as part of the
conda environment creation process.
That means that the package is installed from the cloned repo via symlinks so that
it will be automatically updated as the repo evolves.

.. _editable install mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs

To deactivate the environment use:

.. code-block:: bash

    (moad-tools)$ conda deactivate


.. _moad_toolsCodingStyle:

Coding Style
============

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter

The :py:obj:`moad_tools` package uses the `black`_ code formatting tool to maintain
a coding style that is very close to `PEP 8`_.

.. _black: https://black.readthedocs.io/en/stable/
.. _PEP 8: https://peps.python.org/pep-0008/

:command:`black` is installed as part of the :ref:`moad_toolsDevelopmentEnvironment` setup.

To run :command:`black` on the entire code-base use:

.. code-block:: bash

    $ cd moad_tools
    $ conda activate moad-tools
    (moad-tools)$ black ./

in the repository root directory.
The output looks something like::

  reformatted /media/doug/warehouse/MOAD/moad_tools/docs/conf.py
  reformatted /media/doug/warehouse/MOAD/moad_tools/moad_tools/observations.py
  All done! ✨ 🍰 ✨
  2 files reformatted, 5 files left unchanged.


.. _moad_toolsDocumentation:

Documentation
=============

.. image:: https://readthedocs.org/projects/ubc-moad-tools/badge/?version=latest
    :target: https://ubc-moad-tools.readthedocs.io/en/latest/
    :alt: Documentation Status

The ::py:obj:`moad_tools` documentation is written in `reStructuredText`_ and
converted to HTML using `Sphinx`_.

.. _reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _Sphinx: https://www.sphinx-doc.org/en/master/

If you have write access to the `repository`_ on GitHub,
whenever you push changes to GitHub the documentation is automatically re-built and rendered at https://ubc-moad-tools.readthedocs.io/en/latest/.

Additions,
improvements,
and corrections to these docs are *always* welcome.

The quickest way to fix typos, etc. on existing pages is to use the :guilabel:`Edit on GitHub` link in the upper right corner of the page to get to the online editor for the page on `GitHub`_.

.. _GitHub: https://github.com/UBC-MOAD/moad_tools

For more substantial work,
and to add new pages,
follow the instructions in the :ref:`moad_toolsDevelopmentEnvironment` section above.
In the development environment you can build the docs locally instead of having to push commits to GitHub to trigger a `build on readthedocs.org`_ and wait for it to complete.
Below are instructions that explain how to:

.. _build on readthedocs.org: https://readthedocs.org/projects/ubc-moad-tools/builds/

* build the docs with your changes,
  and preview them in Firefox

* check the docs for broken links


.. _moad_toolsBuildingAndPreviewingTheDocumentation:

Building and Previewing the Documentation
-----------------------------------------

Building the documentation is driven by the :file:`docs/Makefile`.
With your ``moad-tools`` environment activated,
use:

.. code-block:: bash

    (moad-tools)$ cd moad_tools/docs/
    (moad-tools) docs$ make clean html

to do a clean build of the documentation.
The output looks something like:

.. code-block:: text

    Removing everything under '_build'...
    Running Sphinx v7.2.6
    making output directory... done
    loading intersphinx inventory from https://mohid-cmd.readthedocs.io/en/latest/objects.inv...
    loading intersphinx inventory from https://numpy.org/doc/1.18/objects.inv...
    loading intersphinx inventory from https://pandas.pydata.org/docs/objects.inv...
    loading intersphinx inventory from https://docs.python.org/3/objects.inv...
    loading intersphinx inventory from https://rasterio.readthedocs.io/en/latest/objects.inv...
    loading intersphinx inventory from https://shapely.readthedocs.io/en/latest/objects.inv...
    loading intersphinx inventory from https://xarray.pydata.org/en/stable/objects.inv...
    intersphinx inventory has moved: https://xarray.pydata.org/en/stable/objects.inv -> https://docs.xarray.dev/en/stable/objects.inv
    building [mo]: targets for 0 po files that are out of date
    writing output...
    building [html]: targets for 3 source files that are out of date
    updating environment: [new config] 3 added, 0 changed, 0 removed
    reading sources... [100%] pkg_development
    looking for now-outdated files... none found
    pickling environment... done
    checking consistency... done
    preparing documents... done
    copying assets... copying static files... done
    copying extra files... done
    done
    writing output... [100%] pkg_development
    generating indices... genindex py-modindex done
    highlighting module code... [100%] moad_tools.observations
    writing additional pages... search done
    dumping search index in English (code: en)... done
    dumping object inventory... done
    build succeeded.

  The HTML pages are in _build/html.

The HTML rendering of the docs ends up in :file:`docs/_build/html/`.
You can open the :file:`index.html` file in that directory tree in your browser to preview the results of the build.
To preview in Firefox from the command-line you can do:

.. code-block:: bash

    (moad-tools) docs$ firefox _build/html/index.html

If you have write access to the `repository`_ on GitHub,
whenever you push changes to GitHub the documentation is automatically re-built and rendered at https://ubc-moad-tools.readthedocs.io/en/latest/.


.. _moad_toolsLinkCheckingTheDocumentation:

Link Checking the Documentation
-------------------------------

.. image:: https://github.com/UBC-MOAD/moad_tools/workflows/sphinx-linkcheck/badge.svg
    :target: https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Asphinx-linkcheck
    :alt: Sphinx linkcheck

Sphinx also provides a link checker utility which can be run to find broken or redirected links in the docs.
With your ``moad-tools`` environment activated,
use:

.. code-block:: bash

    (moad-tools)$ cd moad_tools/docs/
    (moad-tools) docs$ make linkcheck

The output looks something like:

.. code-block:: text

    Running Sphinx v7.2.6
    making output directory... done
    loading pickled environment... done
    building [mo]: targets for 0 po files that are out of date
    writing output...
    building [linkcheck]: targets for 3 source files that are out of date
    updating environment: 0 added, 1 changed, 0 removed
    reading sources... [100%] pkg_development
    looking for now-outdated files... none found
    pickling environment... done
    checking consistency... done
    preparing documents... done
    copying assets... done
    writing output... [100%] pkg_development

    (      moad_tools: line    1) -ignored- https://github.com/MIDOSS/marine_transport_data
    (      moad_tools: line    3) ok        https://docs.python.org/3/library/exceptions.html#KeyError
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/functions.html#float
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/functions.html#int
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/datetime.html#datetime.datetime
    ( pkg_development: line   23) ok        https://black.readthedocs.io/en/stable/
    ( pkg_development: line   23) ok        https://codecov.io/gh/UBC-MOAD/moad_tools/branch/main/graph/badge.svg
    ( pkg_development: line   23) ok        https://app.codecov.io/gh/UBC-MOAD/moad_tools
    ( pkg_development: line  412) ok        https://coverage.readthedocs.io/en/latest/
    ( pkg_development: line   98) ok        https://conda.io/en/latest/
    ( pkg_development: line   98) ok        https://docs.conda.io/en/latest/miniconda.html
    ( pkg_development: line  461) ok        https://docs.github.com/en/actions
    ( pkg_development: line  387) ok        https://docs.pytest.org/en/latest/
    (      moad_tools: line    1) ok        https://docs.google.com/document/d/14hAxrTFpKloy88zRYLL4TiqLwbn8s53MYQeCt6B3MJ4/edit
    ( pkg_development: line   23) ok        https://docs.python.org/3.12/
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/stdtypes.html#dict
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/stdtypes.html#list
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/stdtypes.html#str
    (      moad_tools: line    1) ok        https://docs.python.org/3/library/stdtypes.html#tuple
    (      moad_tools: line    1) ok        https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html#xarray.Dataset
    ( pkg_development: line  476) ok        https://git-scm.com/
    (      moad_tools: line    4) ok        https://docs.google.com/drawings/d/10PM53-UnnILYCAPKU9MxiR-Y4OW0tIMhVzSjaHr-iSc/edit
    (      moad_tools: line    4) ok        https://docs.google.com/drawings/d/1-4gl2yNNWxqXK-IOr4KNZxO-awBC-bNrjRNrt86fykU/edit
    (      moad_tools: line    4) ok        https://docs.google.com/spreadsheets/d/1dlT0JydkFG43LorqgtHle5IN6caRYjf_3qLrUYqANDY/edit
    (           index: line    6) ok        https://github.com/UBC-MOAD/docs/blob/main/CONTRIBUTORS.rst
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools/actions/workflows/codeql-analysis.yaml/badge.svg
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools/actions?query=workflow:codeql-analysis
    ( pkg_development: line  448) ok        https://github.com/UBC-MOAD/moad_tools/actions
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Asphinx-linkcheck
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools/workflows/pytest-with-coverage/badge.svg
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools/issues
    ( pkg_development: line   23) ok        https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&label=Python&logoColor=gold
    ( pkg_development: line   23) ok        https://img.shields.io/badge/license-Apache%202-cb2533.svg
    ( pkg_development: line   23) ok        https://img.shields.io/badge/code%20style-black-000000.svg
    ( pkg_development: line   23) ok        https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    ( pkg_development: line   23) ok        https://img.shields.io/github/issues/UBC-MOAD/moad_tools?logo=github
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools/workflows/sphinx-linkcheck/badge.svg
    (      moad_tools: line   76) ok        https://mohid-cmd.readthedocs.io/en/latest/
    (      moad_tools: line   76) ok        https://mohid-cmd.readthedocs.io/en/latest/monte-carlo.html#monte-carlo-sub-command
    ( pkg_development: line   23) ok        https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Apytest-with-coverage
    (      moad_tools: line    1) ok        https://numpy.org/doc/1.18/reference/random/generator.html#numpy.random.Generator
    (      moad_tools: line    1) ok        https://numpy.org/doc/1.18/reference/generated/numpy.ndarray.html#numpy.ndarray
    (      moad_tools: line    5) ok        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html#pandas.DataFrame
    ( pkg_development: line  114) ok        https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    ( pkg_development: line  137) ok        https://peps.python.org/pep-0008/
    ( pkg_development: line  412) ok        https://pytest-cov.readthedocs.io/en/latest/
    (      moad_tools: line    1) ok        https://rasterio.readthedocs.io/en/latest/api/rasterio.io.html#rasterio.io.DatasetReader
    (           index: line    9) ok        https://www.apache.org/licenses/LICENSE-2.0
    ( pkg_development: line   23) ok        https://ubc-moad-tools.readthedocs.io/en/latest/
    ( pkg_development: line   23) ok        https://readthedocs.org/projects/ubc-moad-tools/badge/?version=latest
    ( pkg_development: line   69) ok        https://www.python.org/
    ( pkg_development: line  188) ok        https://readthedocs.org/projects/ubc-moad-tools/builds/
    ( pkg_development: line  171) ok        https://www.sphinx-doc.org/en/master/
    ( pkg_development: line  171) ok        https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
    ( pkg_development: line  448) ok        https://github.com/UBC-MOAD/moad_tools/commits/main
    (      moad_tools: line    1) ok        https://www.ndbc.noaa.gov/data/realtime2/
    build succeeded.

  Look for any errors in the above output or in _build/linkcheck/output.txt

:command:`make linkcheck` is run monthly via a `scheduled GitHub Actions workflow`_

.. _scheduled GitHub Actions workflow: https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Asphinx-linkcheck


.. _moad_toolsRunningTheUnitTests:

Running the Unit Tests
======================

The test suite for the :py:obj:`moad_tools` package is in :file:`moad_tools/tests/`.
The `pytest`_ tool is used for test parametrization and as the test runner for the suite.

.. _pytest: https://docs.pytest.org/en/latest/

With your ``moad-tools`` development environment activated,
use:

.. code-block:: bash

    (mohid-cmd)$ cd moad_tools/
    (mohid-cmd)$ pytest

to run the test suite.
The output looks something like:

.. code-block:: text

================================================================================================================================================================= test session starts =================================================================================================================================================================
platform linux -- Python 3.12.0, pytest-7.4.3, pluggy-1.3.0
Using --randomly-seed=3176178277
rootdir: /media/doug/warehouse/MOAD/moad_tools
plugins: randomly-3.15.0, cov-4.1.0
collected 89 items

tests/test_random_oil_spills.py .s.......................................................
..............................                                                      [ 97%]
tests/test_observations.py ..                                                       [100%]

============================= 88 passed, 1 skipped in 2.01s =============================

You can monitor what lines of code the test suite exercises using the `coverage.py`_
and `pytest-cov`_ tools with the command:

.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _pytest-cov: https://pytest-cov.readthedocs.io/en/latest/

.. code-block:: bash

    (mohid-cmd)$ cd moad_tools/
    (mohid-cmd)$ pytest --cov=./

The test coverage report will be displayed below the test suite run output.

Alternatively,
you can use

.. code-block:: bash

    (mohid-cmd)$ pytest --cov=./ --cov-report html

to produce an HTML report that you can view in your browser by opening
:file:`moad_tools/htmlcov/index.html`.


.. _moad_toolsContinuousIntegration:

Continuous Integration
----------------------

.. image:: https://github.com/UBC-MOAD/moad_tools/workflows/pytest-with-coverage/badge.svg
    :target: https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Apytest-with-coverage
    :alt: Pytest with Coverage Status
.. image:: https://codecov.io/gh/UBC-MOAD/moad_tools/branch/main/graph/badge.svg
    :target: https://app.codecov.io/gh/UBC-MOAD/moad_tools
    :alt: Codecov Testing Coverage Report

The :py:obj:`moad_tools` package unit test suite is run and a coverage report is generated
whenever changes are pushed to GitHub.
The results are visible on the `repo actions page`_,
from the green checkmarks beside commits on the `repo commits page`_,
or from the green checkmark to the left of the "Latest commit" message on the
`repo code overview page`_ .
The testing coverage report is uploaded to `codecov.io`_

.. _repo actions page: https://github.com/UBC-MOAD/moad_tools/actions
.. _repo commits page: https://github.com/UBC-MOAD/moad_tools/commits/main
.. _repo code overview page: https://github.com/UBC-MOAD/moad_tools
.. _codecov.io: https://app.codecov.io/gh/UBC-MOAD/moad_tools

The `GitHub Actions`_ workflow configuration that defines the continuous integration tasks
is in the :file:`.github/workflows/pytest-with-coverage.yaml` file.

.. _GitHub Actions: https://docs.github.com/en/actions


.. _moad_toolsVersionControlRepository:

Version Control Repository
==========================

.. image:: https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    :target: https://github.com/UBC-MOAD/moad_tools
    :alt: Git on GitHub

The :py:obj:`moad_tools` package code and documentation source files are available
in the ``moad_tools`` `Git`_ repository at https://github.com/UBC-MOAD/moad_tools.

.. _Git: https://git-scm.com/


.. _moad_toolsIssueTracker:

Issue Tracker
=============

.. image:: https://img.shields.io/github/issues/UBC-MOAD/moad_tools?logo=github
    :target: https://github.com/UBC-MOAD/moad_tools/issues
    :alt: Issue Tracker

Development tasks,
bug reports,
and enhancement ideas are recorded and managed in the issue tracker at https://github.com/UBC-MOAD/moad_tools/issues


License
=======

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0

The UBC EOAS MOAD Group moad_tools Python package code and documentation are
copyright 2018 – present by the `UBC EOAS MOAD Group`_ and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.

.. _UBC EOAS MOAD Group: https://github.com/UBC-MOAD/docs/blob/main/CONTRIBUTORS.rst
