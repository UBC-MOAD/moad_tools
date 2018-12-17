# Copyright 2018 The UBC EOAS MOAD Group
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""moad_tools package
"""
from setuptools import find_packages, setup

from moad_tools import __pkg_metadata__

py_versions = ["3", "3.6"]
python_classifiers = [f"Programming Language :: Python :: {py_versions}"]
other_classifiers = [
    f"Development Status :: {__pkg_metadata__.DEV_STATUS}",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: Implementation :: CPython",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Unix",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Education",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
]
try:
    long_description = open("README.rst", "rt").read()
except IOError:
    long_description = ""
install_requires = [
    # see requirements.txt for versions most recently used in development
    "arrow",
    "Click",
    "matplotlib",
    "netCDF4",
    "pandas",
    "tables",  # PyTables
    "xarray",
]

setup(
    name=__pkg_metadata__.PROJECT,
    version=__pkg_metadata__.VERSION,
    description=__pkg_metadata__.DESCRIPTION,
    long_description=long_description,
    author="Doug Latornell",
    author_email="dlatornell@eoas.ubc.ca",
    url="http://ubc-moad-tools.readthedocs.io/en/latest/",
    license="Apache License, Version 2.0",
    classifiers=python_classifiers + other_classifiers,
    platforms=["Linux"],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        hdf5-to-netcdf4=moad_tools.midoss.hdf5_to_netcdf4:cli
    """,
)
