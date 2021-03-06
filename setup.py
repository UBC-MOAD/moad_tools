# Copyright 2018-2020 The UBC EOAS MOAD Group
# and The University of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""moad_tools - UBC EOAS MOAD Group Tools Package
"""
import setuptools


setuptools.setup(
    entry_points={
        "console_scripts": [
            "geotiff-watermask = moad_tools.midoss.geotiff_watermask:cli",
            "hdf5-to-netcdf4 = moad_tools.midoss.hdf5_to_netcdf4:cli",
            "random-oil-spills = moad_tools.midoss.random_oil_spills:cli",
        ]
    }
)
