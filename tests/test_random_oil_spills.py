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
"""Unit tests for random_oil_spills module.
"""
import logging
import textwrap

from moad_tools.midoss import random_oil_spills


class TestRandomOilSpills:
    """Unit tests for random_oil_spills() function.
    """

    def test_read_config(self, caplog, tmp_path):
        config_file = tmp_path / "random_oil_spills.yaml"
        config_file.write_text(
            textwrap.dedent(
                """\
                """
            )
        )
        caplog.set_level(logging.INFO)

        random_oil_spills.random_oil_spills(1, str(config_file))

        assert caplog.records[0].levelname == "INFO"
        assert caplog.messages[0] == f"read config dict from {config_file}"


class TestWriteCSVFile:
    """Unit tests for write_csv_file() function.
    """

    def test_write_csv_file(self):
        assert True
