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

*************************************
:kbd:`moad_tools` Package Development
*************************************

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
    :target: https://docs.python.org/3.10/
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

The UBC EOAS MOAD Group Tools package (:kbd:`moad_tools`) is a collection of
Python modules that facilitate code reuse for the UBC EOAS MOAD Group.


.. _moad_toolsPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
    :target: https://docs.python.org/3.10/
    :alt: Python Version

The :kbd:`moad_tools` package is developed using `Python`_ 3.10.
It is tested for Python versions >=3.8.
The package uses some Python language features that are not available in versions prior to 3.8,
in particular:

* `formatted string literals`_
  (aka *f-strings*)
  with :kbd:`=` specifiers

.. _Python: https://www.python.org/
.. _formatted string literals: https://docs.python.org/3/reference/lexical_analysis.html#f-strings


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
you can create and activate an environment called :kbd:`moad-tools` that will have
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

The :kbd:`moad_tools` package uses the `black`_ code formatting tool to maintain a coding style that is very close to `PEP 8`_.

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

The ::kbd:`moad_tools` documentation is written in `reStructuredText`_ and converted to HTML using `Sphinx`_.

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
With your :kbd:`moad-tools` environment activated,
use:

.. code-block:: bash

    (moad-tools)$ cd moad_tools/docs/
    (moad-tools) docs$ make clean html

to do a clean build of the documentation.
The output looks something like::

  Removing everything under '_build'...
  Running Sphinx v3.1.1
  making output directory... done
  loading intersphinx inventory from https://mohid-cmd.readthedocs.io/en/latest/objects.inv...
  loading intersphinx inventory from https://numpy.org/doc/1.18/objects.inv...
  loading intersphinx inventory from https://pandas.pydata.org/docs/objects.inv...
  loading intersphinx inventory from https://docs.python.org/3/objects.inv...
  loading intersphinx inventory from https://rasterio.readthedocs.io/en/latest/objects.inv...
  loading intersphinx inventory from https://xarray.pydata.org/en/stable/objects.inv...
  building [mo]: targets for 0 po files that are out of date
  building [html]: targets for 3 source files that are out of date
  updating environment: [new config] 3 added, 0 changed, 0 removed
  reading sources... [100%] pkg_development
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [100%] pkg_development
  generating indices...  genindex py-modindexdone
  highlighting module code... [100%] moad_tools.observations
  writing additional pages...  searchdone
  copying static files... ... done
  copying extra files... done
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
With your :kbd:`moad-tools` environment activated,
use:

.. code-block:: bash

    (moad-tools)$ cd moad_tools/docs/
    (moad-tools) docs$ make linkcheck

The output looks something like::

  Running Sphinx v3.1.1
  making output directory... done
  loading intersphinx inventory from https://mohid-cmd.readthedocs.io/en/latest/objects.inv...
  loading intersphinx inventory from https://numpy.org/doc/1.18/objects.inv...
  loading intersphinx inventory from https://pandas.pydata.org/docs/objects.inv...
  loading intersphinx inventory from https://docs.python.org/3/objects.inv...
  loading intersphinx inventory from https://rasterio.readthedocs.io/en/latest/objects.inv...
  loading intersphinx inventory from https://xarray.pydata.org/en/stable/objects.inv...
  building [mo]: targets for 0 po files that are out of date
  building [linkcheck]: targets for 3 source files that are out of date
  updating environment: [new config] 3 added, 0 changed, 0 removed
  reading sources... [100%] pkg_development
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [ 33%] index
  (line    6) ok        https://www.apache.org/licenses/LICENSE-2.0
  (line    4) ok        https://github.com/UBC-MOAD/docs/blob/main/CONTRIBUTORS.rst
  writing output... [ 66%] moad_tools
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line    1) ok        https://www.ndbc.noaa.gov/data/realtime2/
  (line    3) ok        https://docs.python.org/3/library/exceptions.html#KeyError
  (line   30) ok        https://docs.python.org/3/library/functions.html#int
  (line   51) ok        https://rasterio.readthedocs.io/en/latest/api/rasterio.io.html#rasterio.io.DatasetReader
  (line   51) ok        https://numpy.org/doc/1.18/reference/generated/numpy.ndarray.html#numpy.ndarray
  (line   51) ok        https://numpy.org/doc/1.18/reference/generated/numpy.ndarray.html#numpy.ndarray
  (line   60) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
  (line   60) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
  (line   51) ok        https://xarray.pydata.org/en/stable/generated/xarray.Dataset.html#xarray.Dataset
  (line   73) ok        https://mohid-cmd.readthedocs.io/en/latest/monte-carlo.html#monte-carlo-sub-command
  (line   73) ok        https://mohid-cmd.readthedocs.io/en/latest/
  (line    5) ok        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html#pandas.DataFrame
  (line   30) ok        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html#pandas.DataFrame
  (line  165) ok        https://numpy.org/doc/1.18/reference/random/generator.html#numpy.random.Generator
  (line  165) ok        https://numpy.org/doc/1.18/reference/random/generator.html#numpy.random.Generator
  (line  165) ok        https://docs.python.org/3/library/functions.html#float
  (line  165) ok        https://docs.python.org/3/library/datetime.html#datetime.datetime
  (line  165) ok        https://docs.python.org/3/library/datetime.html#datetime.datetime
  (line  165) ok        https://docs.python.org/3/library/datetime.html#datetime.datetime
  (line  165) ok        https://docs.python.org/3/library/constants.html#None
  (line  165) ok        https://docs.python.org/3/library/stdtypes.html#tuple
  (line  165) ok        https://docs.python.org/3/library/stdtypes.html#list
  writing output... [100%] pkg_development
  (line   21) ok        https://docs.python.org/3.10/
  (line   21) ok        https://black.readthedocs.io/en/stable/
  (line   21) ok        https://ubc-moad-tools.readthedocs.io/en/latest/
  (line   54) ok        https://www.python.org/
  (line   58) ok        https://docs.python.org/3/reference/lexical_analysis.html#f-strings
  (line   60) ok        https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep519
  (line   21) ok        https://github.com/UBC-MOAD/moad_tools
  (line   70) ok        https://github.com/UBC-MOAD/moad_tools
  (line   76) ok        https://github.com/UBC-MOAD/moad_tools
  (line   90) ok        https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh
  (line   21) ok        https://www.apache.org/licenses/LICENSE-2.0
  (line   21) ok        https://github.com/UBC-MOAD/moad_tools/issues
  (line  136) ok        https://www.python.org/dev/peps/pep-0008/
  (line  169) ok        https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
  (line  169) ok        https://www.sphinx-doc.org/en/master/
  (line  360) ok        https://docs.pytest.org/en/latest/
  (line  385) ok        https://coverage.readthedocs.io/en/latest/
  (line  385) ok        https://pytest-cov.readthedocs.io/en/latest/
  (line  101) ok        https://docs.conda.io/en/latest/miniconda.html
  (line  101) ok        https://conda.io/en/latest/
  (line  101) ok        https://www.anaconda.com/products/individual
  (line  185) ok        https://readthedocs.org/projects/ubc-moad-tools/builds/
  (line  410) ok        https://codecov.io/gh/UBC-MOAD/moad_tools
  (line  430) ok        https://docs.github.com/en/actions
  (line  444) ok        https://git-scm.com/
  (line  419) ok        https://codecov.io/gh/UBC-MOAD/moad_tools
  (line   21) ok        https://img.shields.io/badge/license-Apache%202-cb2533.svg
  (line   21) ok        https://img.shields.io/badge/python-3.8+-blue.svg
  (line   21) ok        https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
  (line   21) ok        https://img.shields.io/badge/code%20style-black-000000.svg
  (line   21) ok        https://readthedocs.org/projects/ubc-moad-tools/badge/?version=latest
  (line  410) ok        https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Apytest-with-coverage
  (line  419) ok        https://github.com/UBC-MOAD/moad_tools/actions
  (line  410) ok        https://github.com/UBC-MOAD/moad_tools/workflows/pytest-with-coverage/badge.svg
  (line   21) ok        https://img.shields.io/github/issues/UBC-MOAD/moad_tools?logo=github
  (line  419) ok        https://github.com/UBC-MOAD/moad_tools/commits/main
  (line  410) ok        https://codecov.io/gh/UBC-MOAD/moad_tools/branch/main/graph/badge.svg
  (line  452) ok        https://img.shields.io/github/issues/UBC-MOAD/moad_tools?logo=github

  build succeeded.

  Look for any errors in the above output or in _build/linkcheck/output.txt

:command:`make linkcheck` is run monthly via a `scheduled GitHub Actions workflow`_

.. _scheduled GitHub Actions workflow: https://github.com/UBC-MOAD/moad_tools/actions?query=workflow%3Asphinx-linkcheck


.. _moad_toolsRunningTheUnitTests:

Running the Unit Tests
======================

The test suite for the :kbd:`moad_tools` package is in :file:`moad_tools/tests/`.
The `pytest`_ tool is used for test parametrization and as the test runner for the suite.

.. _pytest: https://docs.pytest.org/en/latest/

With your :kbd:`moad-tools` development environment activated,
use:

.. code-block:: bash

    (mohid-cmd)$ cd moad_tools/
    (mohid-cmd)$ pytest

to run the test suite.
The output looks something like::

  ============================ test session starts ============================
  platform linux -- Python 3.8.3, pytest-5.4.3, py-1.9.0, pluggy-0.13.1
  rootdir: /media/doug/warehouse/MOAD/moad_tools
  collected 11 items
  tests/test_observations.py ..                                          [ 18%]
  tests/test_random_oil_spills.py .........                              [100%]

  ============================ 11 passed in 1.98s =============================

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

The :kbd:`moad_tools` package unit test suite is run and a coverage report is generated
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

The :kbd:`moad_tools` package code and documentation source files are available in the :kbd:`moad_tools` `Git`_ repository at https://github.com/UBC-MOAD/moad_tools.

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
