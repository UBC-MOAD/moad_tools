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
"""Unit tests for observations module.
"""
import urllib
from unittest.mock import patch, Mock

import pytest as pytest

from moad_tools import observations


class TestGetNDBC_Buoy:
    """Unit tests for get_ndbc_buoy().
    """

    @pytest.mark.parametrize("buoy_id", ["foobar"])
    @patch("moad_tools.observations.logging", autospec=True)
    def test_bad_buoy_name(self, m_logging, buoy_id):
        with pytest.raises(KeyError):
            observations.get_ndbc_buoy(buoy_id)
            assert m_logging.error.called

    @pytest.mark.parametrize("buoy_id", [43])
    @patch("moad_tools.observations.logging", autospec=True)
    @patch("moad_tools.observations.pandas.read_table", autospec=True)
    def test_bad_buoy_number(self, m_read_table, m_logging, buoy_id):
        m_read_table.side_effect = urllib.error.HTTPError(
            "http://", 404, "Not Found", "headers", Mock(name="fp")
        )
        with pytest.raises(ValueError):
            observations.get_ndbc_buoy(buoy_id)
            assert m_logging.error.called
