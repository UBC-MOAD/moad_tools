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
from types import SimpleNamespace

import arrow
import numpy
import pandas
import pytest

from moad_tools.midoss import random_oil_spills


@pytest.fixture
def mock_calc_vte_probability(monkeypatch):
    def calc_vte_probability(geotiffs_dir, geotiff_watermask):
        return numpy.array(
            [
                0.06782271,
                0.06652719,
                0.08085802,
                0.07567714,
                0.09073167,
                0.09065133,
                0.09295456,
                0.09669558,
                0.09007693,
                0.08823724,
                0.08245495,
                0.07731268,
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
                geotiff watermask: AIS/ShipTrackDensityGeoTIFFs/geotiff-watermask.npy
                """
            )
        )
        return str(config_file)

    @pytest.fixture
    def mock_numpy_load(self, monkeypatch):
        def numpy_load(path):
            pass

        monkeypatch.setattr(random_oil_spills.numpy, "load", numpy_load)

    @pytest.fixture
    def mock_get_lat_lon_indices(self, monkeypatch):
        def get_lat_lon_indices(
            geotiff_directory,
            spill_month,
            n_locations,
            upsample_factor,
            random_generator,
        ):
            return (
                numpy.array([-123.3461]),
                numpy.array([48.8467]),
                numpy.array([238]),
                numpy.array([478]),
                "data_out",
            )

        monkeypatch.setattr(
            random_oil_spills, "get_lat_lon_indices", get_lat_lon_indices
        )

    def test_read_config(
        self,
        mock_numpy_load,
        mock_calc_vte_probability,
        mock_get_lat_lon_indices,
        config_file,
        caplog,
        tmp_path,
        monkeypatch,
    ):
        caplog.set_level(logging.INFO)

        random_oil_spills.random_oil_spills(1, config_file)

        assert caplog.records[0].levelname == "INFO"
        assert caplog.messages[0] == f"read config dict from {config_file}"

    def test_dataframe_one_row(
        self,
        mock_numpy_load,
        mock_calc_vte_probability,
        mock_get_lat_lon_indices,
        config_file,
        caplog,
        tmp_path,
        monkeypatch,
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
        self,
        mock_numpy_load,
        mock_calc_vte_probability,
        mock_get_lat_lon_indices,
        config_file,
        caplog,
        tmp_path,
        monkeypatch,
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
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_generator = numpy.random.default_rng(seed=43)

        spill_date_hour = random_oil_spills.get_date(
            start_date, end_date, mock_calc_vte_probability, random_generator
        )

        assert spill_date_hour == arrow.get("2017-07-19 21:00").datetime


class TestGetLatLonIndices:
    """Unit tests for get_lat_lon_indices() function.
    """

    @pytest.mark.parametrize(
        "upsample_factor, expected",
        (
            (
                1,
                SimpleNamespace(
                    lat=-123.3461, lon=48.8467, geotiff_x_index=238, geotiff_y_index=478
                ),
            ),
        ),
    )
    def test_get_lat_lon_indices(self, upsample_factor, expected):
        geotiffs_dir = Path("tests/test_data/random_oil_spills/")
        spill_date_hour = arrow.get("2016-08-19 18:00").datetime
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_generator = numpy.random.default_rng(seed=43)

        lats, lons, x_index, y_index, _ = random_oil_spills.get_lat_lon_indices(
            geotiffs_dir,
            spill_date_hour.month,
            n_locations=1,
            upsample_factor=upsample_factor,
            random_generator=random_generator,
        )

        numpy.testing.assert_array_equal(lats, numpy.array([expected.lat]))
        numpy.testing.assert_array_equal(lons, numpy.array([expected.lon]))
        numpy.testing.assert_array_equal(
            x_index, numpy.array([expected.geotiff_x_index])
        )
        numpy.testing.assert_array_equal(
            y_index, numpy.array([expected.geotiff_y_index])
        )


class TestChooseFractionSpilled:
    """Unit test for choose_fraction_spilled() function.
    """

    def test_choose_fraction_spilled(self):
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_generator = numpy.random.default_rng(seed=101)

        spill_fraction = random_oil_spills.choose_fraction_spilled(random_generator)

        assert spill_fraction == pytest.approx(0.63)


class TestCumulativeSpillFraction:
    """Unit test for _cumulative_spill_fraction() function.
    """

    def test_cumulative_spill_fraction(self):
        nbins = 50
        fraction = numpy.linspace(0, 1, num=nbins + 1)

        cumulative = random_oil_spills._cumulative_spill_fraction(fraction)

        expected = numpy.array(
            [
                0,
                0.24266816,
                0.35966341,
                0.42851504,
                0.47787627,
                0.51841066,
                0.55415534,
                0.58670183,
                0.61673461,
                0.64459766,
                0.67050337,
                0.69460976,
                0.71704939,
                0.73794026,
                0.75739031,
                0.77549928,
                0.79235978,
                0.80805793,
                0.82267388,
                0.83628224,
                0.84895248,
                0.86074926,
                0.87173281,
                0.88195918,
                0.89148058,
                0.90034559,
                0.90859948,
                0.91628437,
                0.92343948,
                0.93010134,
                0.93630395,
                0.94207896,
                0.94745587,
                0.9524621,
                0.95712322,
                0.96146302,
                0.96550364,
                0.96926571,
                0.97276844,
                0.97602969,
                0.97906613,
                0.98189324,
                0.98452546,
                0.98697622,
                0.98925803,
                0.99138254,
                0.9933606,
                0.99520229,
                0.99691702,
                0.99851354,
                1,
            ]
        )
        numpy.testing.assert_allclose(cumulative, expected)


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
