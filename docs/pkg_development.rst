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


.. _moad_toolsPackagedDevelopment:

*************************************
:kbd:`moad_tools` Package Development
*************************************

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/python-3.6+-blue.svg
    :target: https://docs.python.org/3.8/
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
.. image:: https://img.shields.io/github/issues/SalishSeaCast/SalishSeaNowcast?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaNowcast/issues
    :alt: Issue Tracker

The UBC EOAS MOAD Group Tools package (:kbd:`moad_tools`) is a collection of Python modules that facilitate code reuse for the UBC EOAS MOAD Group.


.. _moad_toolsPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/badge/python-3.6+-blue.svg
    :target: https://docs.python.org/3.8/
    :alt: Python Version

The :kbd:`moad_tools` package is developed and tested using `Python`_ 3.8 or later.
The package uses some Python language features that are not available in versions prior to 3.6,
in particular:

* `formatted string literals`_
  (aka *f-strings*)
* the `file system path protocol`_

.. _Python: https://www.python.org/
.. _formatted string literals: https://docs.python.org/3/reference/lexical_analysis.html#f-strings
.. _file system path protocol: https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep519


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

or

.. code-block:: bash

    $ git clone https://github.com/UBC-MOAD/moad_tools.git

if you don't have `ssh key authentication`_ set up on GitHub
(replace :kbd:`you_userid` with you GitHub userid,
or copy the link from the :guilabel:`Clone or download` button on the `repository`_ page).

.. _ssh key authentication: https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh


.. _moad_toolsDevelopmentEnvironment:

Development Environment
=======================

Setting up an isolated development environment using `Conda`_ is recommended.
Assuming that you have the `Anaconda Python Distribution`_ or `Miniconda3`_ installed,
you can create and activate an environment called :kbd:`moad-tools` that will have all of the Python packages necessary for development,
testing,
and building the documentation with the commands below:

.. _Conda: https://conda.io/docs/
.. _Anaconda Python Distribution: https://www.anaconda.com/download/
.. _Miniconda3: https://conda.io/docs/install/quick.html

.. code-block:: bash

    $ cd moad_tools
    $ conda env create -f environment-dev.yaml
    $ conda activate moad-tools
    (moad-tools)$ pip install --editable .

The :kbd:`--editable` option in the :command:`pip install` command above installs the :kbd:`moad_tools` package via a symlink so that the installed package will be automatically updated as the repo evolves.

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
.. _PEP 8: https://www.python.org/dev/peps/pep-0008/

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

.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _Sphinx: http://www.sphinx-doc.org/en/master/

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
  Running Sphinx v1.7.4
  making output directory...
  loading pickled environment... not yet created
  loading intersphinx inventory from https://docs.python.org/objects.inv...
  intersphinx inventory has moved: https://docs.python.org/objects.inv -> https://docs.python.org/3/objects.inv
  building [mo]: targets for 0 po files that are out of date
  building [html]: targets for 4 source files that are out of date
  updating environment: 4 added, 0 changed, 0 removed
  reading sources... [100%] pkg_development
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [100%] pkg_development
  generating indices... genindex py-modindex
  highlighting module code... [100%] moad_tools.observations
  writing additional pages... search
  copying static files... done
  copying extra files... done
  dumping search index in English (code: en) ... done
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

Sphinx also provides a link checker utility which can be run to find broken or redirected links in the docs.
With your :kbd:`moad-tools` environment activated,
use:

.. code-block:: bash

    (moad-tools)$ cd moad_tools/docs/
    (moad-tools) docs$ make linkcheck

The output looks something like::

  Running Sphinx v1.7.4
  making output directory...
  loading pickled environment... done
  building [mo]: targets for 0 po files that are out of date
  building [linkcheck]: targets for 4 source files that are out of date
  updating environment: 0 added, 0 changed, 0 removed
  looking for now-outdated files... none found
  preparing documents... done
  writing output... [ 25%] index
  (line    6) ok        http://www.apache.org/licenses/LICENSE-2.0
  (line    4) ok        https://bitbucket.org/UBC_MOAD/docs/src/tip/CONTRIBUTORS.rst
  writing output... [ 50%] moad_tools
  (line    3) ok        https://docs.python.org/3/library/exceptions.html#KeyError
  (line    8) ok        https://docs.python.org/3/library/functions.html#int
  (line    1) ok        https://www.ndbc.noaa.gov/data/realtime2/
  writing output... [ 75%] modules
  writing output... [100%] pkg_development
  (line   21) ok        https://docs.python.org/3.6/
  (line   21) ok        https://black.readthedocs.io/en/stable/
  (line   21) ok        https://ubc-moad-tools.readthedocs.io/en/latest/
  (line   54) ok        https://www.python.org/
  (line   58) ok        https://docs.python.org/3/reference/lexical_analysis.html#f-strings
  (line   60) ok        https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep519
  (line   21) ok        https://github.com/UBC-MOAD/moad_tools/issues?status=new&status=open
  (line   21) ok        https://www.apache.org/licenses/LICENSE-2.0
  (line   90) ok        https://confluence.atlassian.com/bitbucket/set-up-an-ssh-key-728138079.html
  (line   70) ok        https://github.com/UBC-MOAD/moad_tools/
  (line   21) ok        https://github.com/UBC-MOAD/moad_tools/
  (line  102) ok        https://www.anaconda.com/download/
  (line   76) ok        https://github.com/UBC-MOAD/moad_tools/
  (line  102) ok        https://conda.io/docs/
  (line  102) ok        https://conda.io/docs/install/quick.html
  (line   90) ok        https://github.com/UBC-MOAD/moad_tools/
  (line  137) ok        https://www.python.org/dev/peps/pep-0008/
  (line  170) ok        http://www.sphinx-doc.org/en/master/
  (line  170) ok        http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
  (line  186) ok        https://readthedocs.org/projects/ubc-moad-tools/builds/

  build succeeded.

  Look for any errors in the above output or in _build/linkcheck/output.txt


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

.. image:: https://img.shields.io/github/issues/SalishSeaCast/SalishSeaNowcast?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaNowcast/issues
    :alt: Issue Tracker

Development tasks,
bug reports,
and enhancement ideas are recorded and managed in the issue tracker at https://github.com/SalishSeaCast/SalishSeaNowcast/issues


License
=======

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0

The UBC EOAS MOAD Group moad_tools Python package code and documentation are copyright 2018-2020 by the `UBC EOAS MOAD Group`_ and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.

.. _UBC EOAS MOAD Group: https://github.com/UBC-MOAD/docs/blob/master/CONTRIBUTORS.rst
