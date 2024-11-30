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


"""Unit tests for observations module.
"""
import urllib.error
from unittest.mock import Mock, patch

import pytest

from moad_tools import observations


class TestGetNDBC_Buoy:
    """Unit tests for get_ndbc_buoy()."""

    @pytest.mark.parametrize("buoy_id", ["foobar"])
    def test_bad_buoy_name(self, buoy_id, caplog):
        caplog.set_level("DEBUG")

        with pytest.raises(KeyError):
            observations.get_ndbc_buoy(buoy_id)

        assert caplog.records[0].levelname == "ERROR"
        expected = (
            f"buoy id not found in places.PLACES: {buoy_id}; "
            f"maybe try an integer buoy number?"
        )
        assert caplog.records[0].message == expected

    @pytest.mark.parametrize("buoy_id", [43])
    @patch("moad_tools.observations.pandas.read_table", autospec=True)
    def test_bad_buoy_number(self, m_read_table, buoy_id, caplog):
        m_read_table.side_effect = urllib.error.HTTPError(
            "http://", 404, "Not Found", "headers", Mock(name="fp")
        )
        caplog.set_level("DEBUG")

        with pytest.raises(ValueError):
            observations.get_ndbc_buoy(buoy_id)

        assert caplog.records[1].levelname == "ERROR"
        expected = (
            "buoy data request failed: HTTP Error 404: Not Found: "
            "http://www.ndbc.noaa.gov/data/realtime2/43.txt"
        )
        assert caplog.records[1].message == expected
