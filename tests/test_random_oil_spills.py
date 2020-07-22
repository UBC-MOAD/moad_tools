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
import shapely.geometry
import xarray
import yaml

from moad_tools.midoss import random_oil_spills


@pytest.fixture
def config_file(tmp_path):
    test_data = Path(__file__).parent.joinpath("test_data", "random_oil_spills")
    geotiffs_dir = test_data
    shapefiles_dir = test_data
    geotiff_watermask = geotiffs_dir / "geotiff-watermask.npy"
    ssc_mesh = test_data / "mesh_mask201702.nc"
    config_file = tmp_path / "random_oil_spills.yaml"
    config_file.write_text(
        textwrap.dedent(
            f"""\
            start date: 2015-01-01
            end date: 2018-12-31

            geotiffs dir: {geotiffs_dir}
            shapefiles dir: {shapefiles_dir}
            geotiff watermask: {geotiff_watermask}

            nemo meshmask: {ssc_mesh}

            vessel types:
              - tanker
              - atb
              - barge
              - cargo
              - cruise
              - ferry
              - fishing
              - smallpass
              - other
            """
        )
    )
    return str(config_file)


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


@pytest.fixture
def mock_get_length_origin_destination(monkeypatch):
    def get_length_origin_destination(
        shapefiles_dir,
        vessel_type,
        spill_month,
        spill_lat,
        spill_lon,
        random_generator,
    ):
        return 16, None, None

    monkeypatch.setattr(
        random_oil_spills,
        "get_length_origin_destination",
        get_length_origin_destination,
    )


class TestRandomOilSpills:
    """Unit tests for random_oil_spills() function.
    """

    def test_read_config(
        self,
        mock_calc_vte_probability,
        mock_get_length_origin_destination,
        config_file,
        caplog,
        tmp_path,
        monkeypatch,
    ):
        caplog.set_level(logging.INFO)

        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_oil_spills.random_oil_spills(1, config_file, random_seed=43)

        assert caplog.records[0].levelname == "INFO"
        assert caplog.messages[0] == f"read config dict from {config_file}"

    def test_dataframe_one_row(
        self,
        mock_calc_vte_probability,
        mock_get_length_origin_destination,
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
                "spill_lon": [-124.6175],
                "spill_lat": [50.40640],
                "geotiff_x_index": [134],
                "geotiff_y_index": [393],
            }
        )
        pandas.testing.assert_frame_equal(df, expected)

    @pytest.mark.xfail(
        reason="2nd dataframe row changes every time a random_generator.choice() call is added; "
        "finalize when script is complete"
    )
    def test_dataframe_two_rows(
        self,
        mock_calc_vte_probability,
        mock_get_length_origin_destination,
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
                    pandas.Timestamp(arrow.get("2018-08-27 15:00").datetime),
                ],
                "run_days": [7, 7],
                "spill_lon": [-124.6175, -123.0092],
                "spill_lat": [50.4064, 48.5654],
                "geotiff_x_index": [134, 256],
                "geotiff_y_index": [393, 500],
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
    """Unit test for get_lat_lon_indices() function.
    """

    def test_get_lat_lon_indices(self, config_file):
        with Path(config_file).open("r") as f:
            config = yaml.safe_load(f)
        geotiffs_dir = Path(config["geotiffs dir"])
        spill_date_hour = arrow.get("2016-08-19 18:00").datetime
        geotiff_watermask = numpy.load(
            Path(config["geotiff watermask"]), allow_pickle=False, fix_imports=False
        )
        ssc_mesh = xarray.open_dataset(Path(config["nemo meshmask"]))
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_generator = numpy.random.default_rng(seed=43)

        (
            lat,
            lon,
            geotiff_x_index,
            geotiff_y_index,
            geotiff_bbox,
            _,
        ) = random_oil_spills.get_lat_lon_indices(
            geotiffs_dir,
            spill_date_hour.month,
            geotiff_watermask,
            ssc_mesh,
            random_generator,
        )

        expected = SimpleNamespace(
            lat=48.756462,
            lon=-123.37341,
            geotiff_x_index=243,
            geotiff_y_index=476,
            geotiff_bbox=shapely.geometry.Polygon(
                [
                    (-123.3762496, 48.7565228),
                    (-123.3612191, 48.7565228),
                    (-123.3612191, 48.7715534),
                    (-123.3762496, 48.7715534),
                    (-123.3762496, 48.7565228),
                ]
            ),
        )
        assert lat == pytest.approx(expected.lat)
        assert lon == pytest.approx(expected.lon)
        assert geotiff_x_index == expected.geotiff_x_index
        assert geotiff_y_index == expected.geotiff_y_index
        assert geotiff_bbox.almost_equals(expected.geotiff_bbox)


class TestGetVesselType:
    """Unit tests for get_vessel_type() function.
    """

    def test_get_vessel_type(self, config_file):
        with Path(config_file).open("r") as f:
            config = yaml.safe_load(f)
        geotiffs_dir = Path(config["geotiffs dir"])
        vessel_types = config["vessel types"]
        spill_date_hour = arrow.get("2016-08-19 18:00").datetime
        geotiff_x_index, geotiff_y_index = 243, 476
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_generator = numpy.random.default_rng(seed=43)

        vessel_type = random_oil_spills.get_vessel_type(
            geotiffs_dir,
            vessel_types,
            spill_date_hour.month,
            geotiff_x_index,
            geotiff_y_index,
            random_generator,
        )

        assert vessel_type == "ferry"


class TestGetLengthOriginDestination:
    """Unit test for get_length_origin_destination() function.
    """

    @pytest.mark.skipif(
        not Path(__file__)
        .parent.joinpath(
            "test_data", "random_oil_spills", "cargo_2018_01", "cargo_2018_01.shp"
        )
        .exists(),
        reason="shapefile is too large to commit, so only run this test in dev where local file is provided",
    )
    def test_get_length_origin_destination(self, config_file):
        with Path(config_file).open("r") as f:
            config = yaml.safe_load(f)
        shapefiles_dir = Path(config["shapefiles dir"])
        vessel_type = "cargo"
        spill_month = 1
        spill_lat = 50.18442
        spill_lon = -124.9243
        # Specifying the random seed makes the random number stream deterministic
        # so that calculated results are repeatable
        random_generator = numpy.random.default_rng(seed=43)

        (
            vessel_len,
            vessel_origin,
            vessel_dest,
        ) = random_oil_spills.get_length_origin_destination(
            shapefiles_dir,
            vessel_type,
            spill_month,
            spill_lat,
            spill_lon,
            random_generator,
        )

        assert vessel_len == 16
        assert vessel_origin is None
        assert vessel_dest is None


class TestAdjustTugTankBargeLength:
    """Unit tests for adjust_tug_tank_barge_length() function.
    """

    @pytest.mark.parametrize(
        "vessel_type, vessel_len",
        (
            ("tanker", 243),
            ("atb", 143),
            ("barge", 243),
            ("cargo", 143),
            ("cruise", 343),
            ("ferry", 143),
            ("fishing", 43),
            ("smallpass", 43),
            ("other", 43),
        ),
    )
    def test_no_adjustment(self, vessel_type, vessel_len):
        random_generator = numpy.random.default_rng()

        vessel_len = random_oil_spills.adjust_tug_tank_barge_length(
            vessel_type, vessel_len, random_generator,
        )

        assert vessel_len == vessel_len

    @pytest.mark.parametrize("vessel_type, vessel_len", (("atb", 43), ("barge", 34),))
    def test_adjustment(self, vessel_type, vessel_len):
        random_generator = numpy.random.default_rng()

        vessel_len = random_oil_spills.adjust_tug_tank_barge_length(
            vessel_type, vessel_len, random_generator,
        )

        assert vessel_len in [147, 172, 178, 206, 207]


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
    """Unit test for write_csv_file() function.
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
