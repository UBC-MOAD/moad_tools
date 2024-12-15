# Copyright 2018 – present The UBC EOAS MOAD Group
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# SPDX-License-Identifier: Apache-2.0


"""Unit tests for hdf5_to_netcdf4 module.
"""
import shlex
import sys

import pytest

try:
    import tables

    tables_imported = True
except ImportError:
    tables_imported = False


@pytest.mark.skipif(
    tables_imported, reason="PyTables package is in the conda environment"
)
class TestNoTablesPackage:
    """Unit tests for handling of PyTables package (called `tables` in imports) not in the conda
    environment.
    """

    def test_module_import_msg(self, monkeypatch):
        # Monkeypatch sys.argv to an empty so that we get an import despite the test being run
        # via pytest from the command line
        monkeypatch.setattr(sys, "argv", [])

        msg = (
            "Please create an environment with `conda env create -f envs/environment-midoss.yaml` "
            "to use the hdf5_to_netcdf4 module or its command-line tool"
        )
        with pytest.raises(ModuleNotFoundError, match=msg):
            # noinspection PyUnresolvedReferences
            import moad_tools.midoss.hdf5_to_netcdf4

    def test_cli_script_msg(self, monkeypatch, capsys):
        # Monkeypatch sys.argv to simulate CLI invocation despite the test being run
        # via pytest from the command line
        monkeypatch.setattr(sys, "argv", shlex.split("hdf5-to-netcdf4 foo.hdf5 foo.nc"))

        msg = (
            "Please create an environment with `conda env create -f envs/environment-midoss.yaml` "
            "to use the hdf5_to_netcdf4 module or its command-line tool\n"
        )
        with pytest.raises(SystemExit) as exc:
            # noinspection PyUnresolvedReferences
            import moad_tools.midoss.hdf5_to_netcdf4

        assert capsys.readouterr().err == msg
        assert exc.value.code == 2
