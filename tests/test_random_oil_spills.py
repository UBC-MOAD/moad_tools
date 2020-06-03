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
from pathlib import Path

import arrow
import numpy
import pandas
import pytest

from moad_tools.midoss import random_oil_spills


@pytest.fixture
def mock_calc_vte_probability(monkeypatch):
    def calc_vte_probability(geotiffs_dir):
        return numpy.array(
            [
                0.06487016,
                0.06428695,
                0.07748246,
                0.07491668,
                0.09257998,
                0.09288003,
                0.09479203,
                0.09825065,
                0.09265614,
                0.0888919,
                0.08229943,
                0.0760936,
            ]
        )

    monkeypatch.setattr(random_oil_spills, "calc_vte_probability", calc_vte_probability)


class TestRandomOilSpills:
    """Unit tests for random_oil_spills() function.
    """

    @pytest.fixture
    def config_file(self, tmp_path):
        config_file = tmp_path / "random_oil_spills.yaml"
        config_file.write_text(
            textwrap.dedent(
                """\
                start date: 2015-01-01
                end date: 2018-12-31

                geotiffs dir: AIS/ShipTrackDensityGeoTIFFs/
                """
            )
        )
        return str(config_file)

    def test_read_config(
        self, mock_calc_vte_probability, config_file, caplog, tmp_path, monkeypatch
    ):
        caplog.set_level(logging.INFO)

        random_oil_spills.random_oil_spills(1, config_file)

        assert caplog.records[0].levelname == "INFO"
        assert caplog.messages[0] == f"read config dict from {config_file}"

    def test_dataframe_one_row(
        self, mock_calc_vte_probability, config_file, caplog, tmp_path, monkeypatch
    ):
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        df = random_oil_spills.random_oil_spills(1, config_file, random_seed=43)

        expected = pandas.DataFrame(
            {
                "spill_date_hour": [
                    pandas.Timestamp(arrow.get("2016-08-19 18:00").datetime)
                ],
                "run_days": [7],
            }
        )
        pandas.testing.assert_frame_equal(df, expected)

    def test_dataframe_two_rows(
        self, mock_calc_vte_probability, config_file, caplog, tmp_path, monkeypatch
    ):
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        df = random_oil_spills.random_oil_spills(2, config_file, random_seed=43)

        expected = pandas.DataFrame(
            {
                "spill_date_hour": [
                    pandas.Timestamp(arrow.get("2016-08-19 18:00").datetime),
                    pandas.Timestamp(arrow.get("2015-01-06 10:00").datetime),
                ],
                "run_days": [7, 7],
            },
        )
        pandas.testing.assert_frame_equal(df, expected)


class TestGetDate:
    """Unit test for get_date() function.
    """

    def test_get_date(self, mock_calc_vte_probability):
        start_date = arrow.get("2015-01-01").datetime
        end_date = arrow.get("2018-12-31").datetime
        vte_probability = random_oil_spills.calc_vte_probability(
            Path("AIS/ShipTrackDensityGeoTIFFs/")
        )
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_generator = numpy.random.default_rng(seed=43)

        spill_date_hour = random_oil_spills.get_date(
            start_date, end_date, vte_probability, random_generator
        )

        assert spill_date_hour == arrow.get("2016-08-19 18:00").datetime


class TestWriteCSVFile:
    """Unit tests for write_csv_file() function.
    """

    def test_write_csv_file(self, tmp_path):
        df = pandas.DataFrame(
            {
                "spill_date_hour": [
                    pandas.Timestamp(arrow.get("2016-08-19 18:00").datetime),
                    pandas.Timestamp(arrow.get("2015-01-06 10:00").datetime),
                ],
                "run_days": [7, 7],
            },
        )
        out_csv = tmp_path / "out.csv"

        random_oil_spills.write_csv_file(df, str(out_csv))

        expected = textwrap.dedent(
            """\
            spill_date_hour,run_days
            2016-08-19 18:00,7
            2015-01-06 10:00,7
            """
        )

        assert out_csv.read_text() == expected
