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
"""Functions and command-line tool to calculate a CSV file containing parameters of a set
of random oil spills to drive Monte Carlo runs of MOHID.
"""
import collections
import datetime
import logging
import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import arrow
import click
import geopandas
import numpy
import pandas
import rasterio
import shapely.geometry
import xarray
import yaml

logging.getLogger(__name__).addHandler(logging.NullHandler())


def random_oil_spills(n_spills, config_file, random_seed=None):
    """Calculate a dataframe containing parameters of a set of random oil spills
    to drive Monte Carlo runs of MOHID.

    :param int n_spills: Number of spills to calculate parameters for.

    :param str config_file: File path and name of the YAML file to read processing configuration
                            dictionary from.

    :param random_seed: Seed to initialize random number generator with.
                        This is facilitates a reproducible stream of random number that is useful
                        for unit testing.
    :type random_seed: None or int

    :return: Dataframe of random oil spill parameters with :kbd:`n_spills` rows.
    :rtype: :py:class:`pandas.DataFrame`
    """
    with Path(config_file).open("rt") as f:
        config = yaml.safe_load(f)
        logging.info(f"read config dict from {config_file}")

    # Load GeoTIFF files for each month and add up vessel traffic exposure (VTE)
    geotiffs_dir = Path(config["geotiffs dir"])
    geotiff_watermask = numpy.load(
        Path(config["geotiff watermask"]), allow_pickle=False, fix_imports=False
    )
    vte_probability = calc_vte_probability(geotiffs_dir, geotiff_watermask)

    # Initialize PCG-64 random number generator
    random_generator = numpy.random.default_rng(random_seed)

    start_date = arrow.get(config["start date"]).datetime
    end_date = arrow.get(config["end date"]).datetime

    ssc_mesh = xarray.open_dataset(Path(config["nemo meshmask"]))

    vessel_types = config["vessel types"]

    shapefiles_dir = Path(config["shapefiles dir"])

    spill_params = collections.defaultdict(list)
    for spill in range(n_spills):
        spill_date_hour = get_date(
            start_date, end_date, vte_probability, random_generator
        )
        spill_params["spill_date_hour"].append(spill_date_hour)
        spill_params["run_days"].append(7)

        (
            spill_lat,
            spill_lon,
            geotiff_x_index,
            geotiff_y_index,
            geotiff_bbox,
            _,
        ) = get_lat_lon_indices(
            geotiffs_dir,
            spill_date_hour.month,
            geotiff_watermask,
            ssc_mesh,
            random_generator,
        )
        spill_params["spill_lon"].append(spill_lon)
        spill_params["spill_lat"].append(spill_lat)
        spill_params["geotiff_x_index"].append(geotiff_x_index)
        spill_params["geotiff_y_index"].append(geotiff_y_index)

        vessel_type = get_vessel_type(
            geotiffs_dir,
            vessel_types,
            spill_date_hour.month,
            geotiff_x_index,
            geotiff_y_index,
            random_generator,
        )

        (
            vessel_len,
            vessel_origin,
            vessel_dest,
            vessel_mmsi,
        ) = get_length_origin_destination(
            shapefiles_dir,
            vessel_type,
            spill_date_hour.month,
            geotiff_bbox,
            random_generator,
        )
        spill_params["vessel_mmsi"].append(vessel_mmsi)
        vessel_len = adjust_tug_tank_barge_length(
            vessel_type, vessel_len, random_generator
        )

        oil_attribution_file = Path(config["oil attribution"])
        with oil_attribution_file.open("rt") as f:
            oil_attrs = yaml.safe_load(f)
        fuel_capacity, cargo_capacity = get_oil_capacity(
            oil_attrs, vessel_len, vessel_type, random_generator
        )
        try:
            fuel_spill = random_generator.choice(
                [False, True],
                p=[
                    oil_attrs["vessel_attributes"][vessel_type]["probability_cargo"],
                    oil_attrs["vessel_attributes"][vessel_type]["probability_fuel"],
                ],
            )
        except KeyError:
            # No probability_cargo or probability_fuel key means that vessel type carries only fuel
            fuel_spill = 1
        max_spill_volume = fuel_capacity if fuel_spill else cargo_capacity
        spill_params["spill_volume"].append(
            max_spill_volume * choose_fraction_spilled(random_generator)
        )

    df = pandas.DataFrame(spill_params)

    return df


def calc_vte_probability(geotiffs_dir, geotiff_watermask):
    """Calculate monthly spill probability weights from vessel traffic exposure (VTE)
    in AIS GeoTIFF files, masked to include only cells that are within the SalishSeaCast
    NEMO domain.

    :param geotiffs_dir: Directory path to read AIS GeoTIFF files from.
    :type geotiffs_dir: :py:class:`pathlib.Path`

    :param geotiff_watermask: Boolean water mask to apply to AIS ship track density GeoTIFF files
                              to restrict them to the SalishSeaCast NEMO domain.
    :type geotiff_watermask: :py:class:`numpy.ndarray`

    :return: 12 elements array of monthly spill probability weights
    :rtype: :py:class:`numpy.ndarray`
    """
    logging.info("Calculating monthly spill probability weights from VTE")
    total_vte_by_month = numpy.empty(12)

    for month in range(1, 13):
        # The filenames are formatted as "all_2018_MM.tif"
        f_name = geotiffs_dir / f"all_2018_{month:02d}.tif"

        with rasterio.open(f_name) as dataset:
            total_vte_by_month[month - 1] = dataset.read(
                boundless=True, fill_value=0
            ).sum(where=geotiff_watermask)

    # calculate VTE probability by month based on total traffic for each month
    vte_probability = total_vte_by_month / total_vte_by_month.sum()

    return vte_probability


def get_date(start_date, end_date, vte_probability, random_generator):
    """Randomly select a spill date and hour, with the month weighted by vessel traffic exposure
    (VTE) probability.

    :param start_date: Starting date of period from which spill dates and hours are to be selected.
    :type start_date: :py:class:`datetime.datetime`

    :param end_date: Ending date of period from which spill dates and hours are to be selected.
    :type end_date: :py:class:`datetime.datetime`

    :param vte_probability: 12 elements array of monthly spill probability weights
    :type vte_probability: :py:class:`numpyt.ndarray`

    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Randomly selected spill date and hour
    :rtype: :py:class:`datetime.datetime`
    """
    logging.info("Selecting random spill date and hour, weighted by VTE")
    # Randomly select month based on weighting by vessel traffic
    month_random = random_generator.choice(range(1, 13), p=vte_probability)

    # Now that month is selected, we need to choose day, year, and time.
    # We weight these all the same.
    time_period = end_date - start_date
    time_period_inhours = numpy.int(time_period.total_seconds() / 3600)
    date_arr = [
        start_date + timedelta(hours=i) for i in range(0, time_period_inhours + 1)
    ]

    # Extract dates in time period for only the month selected as month_random
    date_arr_select = []
    for days in date_arr:
        if days.month == month_random:
            date_arr_select.append(days)

    return random_generator.choice(date_arr_select)


def get_lat_lon_indices(
    geotiffs_dir, spill_month, geotiff_watermask, ssc_mesh, random_generator,
):
    """Randomly select a spill lat/lon based on vessel traffic exposure (VTE)
    in a particular month's AIS GeoTIFF file. The VTE data are masked to include
    only cells that have water cells within the SalishSeaCast NEMO domain.
    The lat/lon from VTE is used to select a SalishSeaCast NEMO surface grid cell
    from which one of 9 uniformly distributed sub-grid points within the cell is
    randomly selected as the spill location.

    :param geotiffs_dir: Directory path to read AIS GeoTIFF files from.
    :type geotiffs_dir: :py:class:`pathlib.Path`

    :param int spill_month: Month number for which to choose a spill location.

    :param geotiff_watermask: Boolean water mask to apply to AIS ship track density GeoTIFF files
                              to restrict them to the SalishSeaCast NEMO domain.
    :type geotiff_watermask: :py:class:`numpy.ndarray`

    :param ssc_mesh: SalishSeaCast NEMO mesh mask dataset to use the NEMO grid lons/lats
                     and T-grid water/land maks from to calculate the water mask.
    :type ssc_mesh: :py:class:`xarray.Dataset`

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: 6-tuple composed of:

             * spill latitude [°N in [-90°, 90°] range]
             * spill longitude [°E in [-180°, 180°] range]
             * x-index of GeoTIFF cell in which spill is located
             * y-index of GeoTIFF cell in which spill is located
             * GeoTIFF cell bounding box
             * value of GeoTIFF cell in which spill is located (for QA/QC)

    :rtype: tuple
    """
    logging.info(
        f"Selecting random spill location within SalishSeaCast domain, "
        f"weighted by 2018-{spill_month:02d} VTE"
    )
    with rasterio.open(geotiffs_dir / f"all_2018_{spill_month:02d}.tif") as dataset:
        data = dataset.read(1, boundless=True, fill_value=0)

        # Zero any points that are non-water or outside the SalishSeaCast domain
        data = data * geotiff_watermask

        # Calculate probability of traffic by VTE in the month
        probability_distribution = data / data.sum()

        # Choose a random GeoTIFF cell, weighted by the month's VTE probability distribution,
        # and calculated the cell's x/y indices
        mp = random_generator.choice(data.size, p=probability_distribution.flatten())
        px = mp // dataset.width
        py = mp % dataset.width

        # Get lats/lons of lower-right and upper-left corners of the chosen GeoTIFF cell
        # and construct its bounding box
        llx, lly = rasterio.transform.xy(dataset.transform, px + 0.5, py - 0.5)
        urx, ury = rasterio.transform.xy(dataset.transform, px - 0.5, py + 0.5)
        geotiff_bbox = shapely.geometry.Polygon(
            [(llx, lly), (urx, lly), (urx, ury), (llx, ury), (llx, lly)]
        )

        # Find the SalishSeaCast T-grid water points in the GeoTIFF cell
        ssc_lons = ssc_mesh.glamt.isel(t=0)
        ssc_lats = ssc_mesh.gphit.isel(t=0)
        ssc_tmask = ssc_mesh.tmask.isel(t=0, z=0)
        inner_points = (
            numpy.where(ssc_tmask == 1, 1, 0)
            * numpy.where(ssc_lons > llx, 1, 0)
            * numpy.where(ssc_lons < urx, 1, 0)
            * numpy.where(ssc_lats > lly, 1, 0)
            * numpy.where(ssc_lats < ury, 1, 0)
        )

        # Choose a random SalishSeaCast T-grid water point, and calculate its lat/lon.
        # The probability distribution here acts as a filter to restrict the choice of
        # SalishSeaCast T-grid points to those that were found above to be within the chosen
        # GeoTIFF cell.
        ssp = random_generator.choice(
            ssc_tmask.size, p=inner_points.flatten() / inner_points.sum(),
        )
        sslon = ssc_lons.values.flat[ssp]
        sslat = ssc_lats.values.flat[ssp]

        # Define nine points in the horizontal plane of a SalishSeaCast T-grid cell,
        # and choose a random one of them.
        # This could be factored out into a separate function to avoid repeatedly building
        # this dict, if performance becomes an issue.
        one_third = 1 / 3
        within_box = {
            "center": SimpleNamespace(dx=0, dy=0),
            "left": SimpleNamespace(dx=one_third, dy=0),
            "uleft": SimpleNamespace(dx=one_third, dy=one_third),
            "upper": SimpleNamespace(dx=0, dy=one_third),
            "uright": SimpleNamespace(dx=-one_third, dy=one_third),
            "right": SimpleNamespace(dx=-one_third, dy=0),
            "lright": SimpleNamespace(dx=-one_third, dy=-one_third),
            "lower": SimpleNamespace(dx=0, dy=-one_third),
            "lleft": SimpleNamespace(dx=one_third, dy=-one_third),
        }
        shift = random_generator.choice(list(within_box.keys()))

        # Calculate the SalishSeaCast T-grid cell size in degrees of lat & lon
        width = ssc_tmask.x.size
        londx, latdx = (
            ssc_lons.values.flat[ssp + 1] - ssc_lons.values.flat[ssp],
            ssc_lats.values.flat[ssp + 1] - ssc_lats.values.flat[ssp],
        )
        londy, latdy = (
            ssc_lons.values.flat[ssp + width] - ssc_lons.values.flat[ssp],
            ssc_lats.values.flat[ssp + width] - ssc_lats.values.flat[ssp],
        )

        # Calculate lat/lon of the spill
        lat = sslat + latdx * within_box[shift].dx + latdy * within_box[shift].dy
        lon = sslon + londx * within_box[shift].dx + londy * within_box[shift].dy

        return lat, lon, px, py, geotiff_bbox, data[px, py]


def get_vessel_type(
    geotiffs_dir,
    vessel_types,
    spill_month,
    geotiff_x_index,
    geotiff_y_index,
    random_generator,
):
    """Randomly choose a vessel type from which the spill occurs, with the choice weighted by the
    vessel traffic exposure (VTE) for the specified month and GeoTIFF cell.

    :param geotiffs_dir: Directory path to read AIS GeoTIFF files from.
    :type geotiffs_dir: :py:class:`pathlib.Path`

    :param list vessel_types: Vessel types from which spill can occur,
                              and for which there are monthly 2018 VTE GeoTIFFs.

    :param int spill_month: Month number for which to choose a spill location.

    :param int geotiff_x_index: x-index of GeoTIFF cell in which spill is located

    :param int geotiff_y_index: y-index of GeoTIFF cell in which spill is located

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Randomly selected vessel type from which spill occurs.
    :rtype: str
    """
    # Calculate vessel traffic exposure (VTE) [hours/km^2] for each vessel type
    # at the spill location for the month in which the spill occurs
    vte_by_vessel_type = numpy.empty(len(vessel_types))
    for i, vessel_type in enumerate(vessel_types):
        geotiff_file = geotiffs_dir / f"{vessel_type}_2018_{spill_month:02d}.tif"
        with rasterio.open(geotiff_file) as dataset:
            data = dataset.read(1, boundless=True, fill_value=0)

        vte_by_vessel_type[i] = data[geotiff_x_index, geotiff_y_index]

    # Choose a random vessel type, weighted by the vessel type VTE probability distribution
    # for the month
    probability = vte_by_vessel_type / vte_by_vessel_type.sum()
    vessel_type = random_generator.choice(vessel_types, p=probability)

    return vessel_type


def get_length_origin_destination(
    shapefiles_dir, vessel_type, spill_month, geotiff_bbox, random_generator,
):
    """Randomly choose an AIS vessel track from which the spill occurs, with the choice
    weighted by the vessel traffic exposure (VTE) for the specified vessel type, month,
    and GeoTIFF cell. Return the length of the vessel, and voyage origin & destination,
    and vessel MMSI from the chosen AIS track.

    :param shapefiles_dir: Directory path to read shapefiles from
    :type shapefiles_dir: :py:class:`pathlib.Path`

    :param str vessel_type: Vessel type from which spill occurs.

    :param int spill_month: Month number in which spill occurs.

    :param geotiff_bbox: Bounding box of GeoTIFF cell containing spill location.
    :type geotiff_bbox: :py:class:`shapely.geometry.Polygon`

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: 4-tuple composed of:

             * length of vessel from which spill occurs [m] (int)
             * origin of AIS track from which spill occurs (str)
             * destination of AIS track from which spill occurs (str)
             * vessel MMSI (str)

    :rtype: tuple
    """
    # Load AIS track segments that pass through or are contained in GeoTIFF cell in which
    # spill occurs
    shapefile = shapefiles_dir / f"{vessel_type}_2018_{spill_month:02d}.shp"
    ais_tracks = geopandas.read_file(shapefile, bbox=geotiff_bbox)

    vte = numpy.empty(len(ais_tracks.index))
    for i, ais_track in ais_tracks.iterrows():
        track_in_cell = ais_track.geometry.intersection(geotiff_bbox)
        # The lengths used here are Cartesian plane lengths,
        # note spherical coordinate distances, but we are working on
        # a small patch of the Earth's surface, and we are using the
        # length construct consistently, so the error is acceptably small.
        frac_in_cell = track_in_cell.length / ais_track.geometry.length
        track_duration = pandas.to_datetime(ais_track.EN_DATE) - pandas.to_datetime(
            ais_track.ST_DATE
        )
        vte[i] = frac_in_cell * track_duration.total_seconds()

    chosen_track_index = random_generator.choice(
        range(len(ais_tracks.index)), p=vte / vte.sum()
    )
    vessel_len = ais_tracks.LENGTH[chosen_track_index]
    try:
        vessel_origin = ais_tracks.FROM_[chosen_track_index]
    except AttributeError:
        vessel_origin = None
    try:
        vessel_dest = ais_tracks.TO[chosen_track_index]
    except AttributeError:
        vessel_dest = None
    # MMSI is a label that happens to be composed of digits
    # Cast it to a str even though it is stored as a float the shapefile
    vessel_mmsi = f"{ais_tracks.MMSI_NUM[chosen_track_index]:.0f}"

    return vessel_len, vessel_origin, vessel_dest, vessel_mmsi


def adjust_tug_tank_barge_length(vessel_type, vessel_len, random_generator):
    """Standardize ATB and tug lengths to represent length of tug and tank barge.
    See `AIS data attribute table`_ for more information.

    .. _AIS data attribute table: https://docs.google.com/document/d/14hAxrTFpKloy88zRYLL4TiqLwbn8s53MYQeCt6B3MJ4/edit

    :param str vessel_type: Vessel type from which spill occurs.

    :param int vessel_len: Length of vessel from which spill occurs [m].

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Randomly selected tug and tank barge length [m].
    :rtype: int
    """
    if vessel_type not in {"atb", "barge"}:
        # Adjustment only applies to ATB and barge vessel types
        return vessel_len
    if vessel_len >= 100:  # meters
        # Adjustment only applies to ATBs and barges <100m in length
        return vessel_len
    return random_generator.choice([147, 172, 178, 206, 207])


def get_oil_capacity(oil_attrs, vessel_length, vessel_type, random_generator):
    """Calculate fuel_capacity [liters] and cargo_capacity [liters] based on vessel
    length and type, with the exception of ATBs and barges.  Tank_capacity
    is estimated by length for ATBs > 50 m only.  For all other ATB and barge
    traffic, as well as fuel capacity for ATBs > 50 m, both fuel and cargo
    capacities are estimated by weighted values based on AIS data for ATB
    ship traffic for which tugs and barges were married by a combination of
    web research and AIS analysis. We assume that the fuel and cargo
    capacities for non-ATB tug and tank barges is well represented by the
    ATB data.

    :param dict oil_attrs: Oil attribution information from the output of make_oil_attrs.py.

    :param int or float vessel_length: Length of vessel from which spill occurs [m].

    :param str vessel_type: Vessel type from which spill occurs.

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`
    """
    if vessel_type not in oil_attrs["categories"]["all_vessels"]:
        raise ValueError(
            [
                "Oops! Vessel type isn't valid."
                + "Today's flavors are: tanker, atb, barge, cargo, cruise, "
                + "ferry, fishing, smallpass, or other.  So..."
                + "Go fish! (or try 'fishing' instead)"
            ]
        )

    if vessel_length < oil_attrs["vessel_attributes"][vessel_type]["min_length"]:
        # set lower bound
        fuel_capacity = oil_attrs["vessel_attributes"][vessel_type]["min_fuel"]
        cargo_capacity = (
            oil_attrs["vessel_attributes"][vessel_type]["min_cargo"]
            if vessel_type in oil_attrs["categories"]["tank_vessels"]
            else 0
        )

    elif vessel_length > oil_attrs["vessel_attributes"][vessel_type]["max_length"]:
        # set upper bound
        fuel_capacity = oil_attrs["vessel_attributes"][vessel_type]["max_fuel"]
        cargo_capacity = (
            oil_attrs["vessel_attributes"][vessel_type]["max_cargo"]
            if vessel_type in oil_attrs["categories"]["tank_vessels"]
            else 0
        )
    else:

        # ~~~ tankers ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if vessel_type == "tanker":

            bins = oil_attrs["vessel_attributes"]["tanker"]["length_bins"]

            if vessel_length >= max(max(bins)):
                cargo_capacity = oil_attrs["vessel_attributes"]["tanker"]["max_cargo"]
                fuel_capacity = oil_attrs["vessel_attributes"]["tanker"]["max_fuel"]

            elif vessel_length < 0:
                cargo_capacity = oil_attrs["vessel_attributes"]["tanker"]["min_cargo"]
                fuel_capacity = oil_attrs["vessel_attributes"]["tanker"]["min_fuel"]
            else:
                bin_index = _get_bin(vessel_length, bins)

                cargo_capacity = oil_attrs["vessel_attributes"]["tanker"][
                    "cargo_capacity"
                ][bin_index]
                fuel_capacity = oil_attrs["vessel_attributes"]["tanker"][
                    "fuel_capacity"
                ][bin_index]

        # ~~~ atbs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "atb":

            atb_min_cargo = oil_attrs["vessel_attributes"]["atb"]["min_cargo"]
            atb_max_cargo = oil_attrs["vessel_attributes"]["atb"]["max_cargo"]

            if vessel_length > 50:
                # For ATB lengths > 50 m, calculate capacity from linear fit
                C = oil_attrs["vessel_attributes"]["atb"]["cargo_fit_coefs"]
                fit_capacity = C[1] + C[0] * vessel_length
                # impose thresholds to yield output capacity
                cargo_capacity = _clamp(fit_capacity, atb_min_cargo, atb_max_cargo)
            else:
                # Use cargo capacity weights by AIS ship track data
                # for lengths < 50 m
                cargo_weight = oil_attrs["vessel_attributes"]["atb"][
                    "cargo_capacity_probability"
                ]
                cargo_capacity_bin_centers = oil_attrs["vessel_attributes"]["atb"][
                    "cargo_capacity_bin_centers"
                ]
                cargo_capacity = random_generator.choice(
                    cargo_capacity_bin_centers, p=cargo_weight
                )

            # for all ATBs, estimate fuel capacity by AIS ship track weighting
            fuel_weight = oil_attrs["vessel_attributes"]["atb"][
                "fuel_capacity_probability"
            ]
            fuel_capacity_bin_centers = oil_attrs["vessel_attributes"]["atb"][
                "fuel_capacity_bin_centers"
            ]
            fuel_capacity = random_generator.choice(
                fuel_capacity_bin_centers, p=fuel_weight
            )

        # ~~~ barges ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "barge":

            cargo_weight = oil_attrs["vessel_attributes"]["barge"][
                "cargo_capacity_probability"
            ]
            cargo_capacity_bin_centers = oil_attrs["vessel_attributes"]["barge"][
                "cargo_capacity_bin_centers"
            ]
            cargo_capacity = random_generator.choice(
                cargo_capacity_bin_centers, p=cargo_weight
            )

            fuel_weight = oil_attrs["vessel_attributes"]["barge"][
                "fuel_capacity_probability"
            ]
            fuel_capacity_bin_centers = oil_attrs["vessel_attributes"]["barge"][
                "fuel_capacity_bin_centers"
            ]
            fuel_capacity = random_generator.choice(
                fuel_capacity_bin_centers, p=fuel_weight
            )

        ###  Fuel capacities below this line are still being evaluated ###
        # ~~~ cargo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "cargo":

            C = oil_attrs["vessel_attributes"]["cargo"]["fuel_fit_coefs"]

            fit_capacity = numpy.exp(C[1]) * numpy.exp(C[0] * vessel_length)

            cargo_capacity = 0

            # impose fuel capacity limits for this vessel type
            min_fuel = oil_attrs["vessel_attributes"]["cargo"]["min_fuel"]
            max_fuel = oil_attrs["vessel_attributes"]["cargo"]["max_fuel"]

            fuel_capacity = _clamp(fit_capacity, min_fuel, max_fuel)

        # ~~~ cruise ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "cruise":

            C = oil_attrs["vessel_attributes"]["cruise"]["fuel_fit_coefs"]

            fit_capacity = C[1] + C[0] * vessel_length

            cargo_capacity = 0

            # impose fuel capacity limits for this vessel type
            min_fuel = oil_attrs["vessel_attributes"]["cruise"]["min_fuel"]
            max_fuel = oil_attrs["vessel_attributes"]["cruise"]["max_fuel"]

            fuel_capacity = _clamp(fit_capacity, min_fuel, max_fuel)

        # ~~~ ferry ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "ferry":

            C = oil_attrs["vessel_attributes"]["ferry"]["fuel_fit_coefs"]

            fit_capacity = numpy.exp(C[1]) * numpy.exp(C[0] * vessel_length)

            cargo_capacity = 0

            # impose fuel capacity limits for this vessel type
            min_fuel = oil_attrs["vessel_attributes"]["ferry"]["min_fuel"]
            max_fuel = oil_attrs["vessel_attributes"]["ferry"]["max_fuel"]

            fuel_capacity = _clamp(fit_capacity, min_fuel, max_fuel)

        # ~~~ fishing ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "fishing":

            C = oil_attrs["vessel_attributes"]["fishing"]["fuel_fit_coefs"]

            fit_capacity = C[2] + C[1] * vessel_length + C[0] * vessel_length ** 2

            cargo_capacity = 0

            # impose fuel capacity limits for this vessel type
            min_fuel = oil_attrs["vessel_attributes"]["fishing"]["min_fuel"]
            max_fuel = oil_attrs["vessel_attributes"]["fishing"]["max_fuel"]

            fuel_capacity = _clamp(fit_capacity, min_fuel, max_fuel)

        # ~~~ small pass ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "smallpass":

            C = oil_attrs["vessel_attributes"]["smallpass"]["fuel_fit_coefs"]

            fit_capacity = numpy.exp(C[1]) * numpy.exp(C[0] * vessel_length)

            cargo_capacity = 0

            # impose fuel capacity limits for this vessel type
            min_fuel = oil_attrs["vessel_attributes"]["smallpass"]["min_fuel"]
            max_fuel = oil_attrs["vessel_attributes"]["smallpass"]["max_fuel"]

            fuel_capacity = _clamp(fit_capacity, min_fuel, max_fuel)

        # ~~~ other ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif vessel_type == "other":

            C = oil_attrs["vessel_attributes"]["other"]["fuel_fit_coefs"]

            fit_capacity = numpy.exp(C[1]) * numpy.exp(C[0] * vessel_length)

            cargo_capacity = 0

            # impose fuel capacity limits for this vessel type
            min_fuel = oil_attrs["vessel_attributes"]["other"]["min_fuel"]
            max_fuel = oil_attrs["vessel_attributes"]["other"]["max_fuel"]

            fuel_capacity = _clamp(fit_capacity, min_fuel, max_fuel)

    return fuel_capacity, cargo_capacity


def _clamp(n, minn, maxn):
    """Returns the number n after fixing min and max thresholds.
    minn and maxn are scalars that represent min and max capacities.
    clamp ensures that capacities are within min/max thresholds
    and sets n to minn or maxn if outside of thresholds, such that
    minn < n < maxn
    """
    if n < minn:
        return minn
    elif n > maxn:
        return maxn
    else:
        return n


def _get_bin(value, bins):
    """Returns the smallest index i of bins so that
    bin[i][0] <= value < bin[i][1], where
    bins is a list of tuples, like [(0,20), (20, 40), (40, 60)]
    """

    for i in range(0, len(bins)):
        if bins[i][0] <= value < bins[i][1]:
            return i
    return -1


def choose_fraction_spilled(random_generator):
    """Randomly choose a fraction spilled based on the _cumulative_spill_fraction() fit.

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Fraction of oil volume spilled.
    :rtype: float
    """
    nbins = 50
    # We need both sides of the bins, so array is nbins+1 long
    fraction = numpy.linspace(0, 1, num=nbins + 1)
    cumulative = _cumulative_spill_fraction(fraction)

    probability = cumulative[1:] - cumulative[:-1]
    central_value = 0.5 * (fraction[1:] + fraction[:-1])

    spill_fraction = random_generator.choice(central_value, p=probability)
    return spill_fraction


def _cumulative_spill_fraction(fraction):
    """Calculate the cumulative spill probability up to fraction based on 10 spill cases from Ryah.

    :param fraction: Spill fraction.
    :type fraction: :py:class:`numpy.ndarray`

    :return: Cumulative spill probability.
    :rtype: :py:class:`numpy.ndarray`
    """
    typeonefrac = 0.7
    typetwofrac = 1 - typeonefrac
    typeonedec = 28 / 100
    typetwodec = 2 / 100
    multiplier = 1 / (
        1
        - typeonefrac * numpy.exp(-1 / typeonedec)
        - typetwofrac * numpy.exp(-1 / typetwodec)
    )
    return (
        1
        - typeonefrac * numpy.exp(-fraction / typeonedec)
        - typetwofrac * numpy.exp(-fraction / typetwodec)
    ) * multiplier


def write_csv_file(df, csv_file):
    """
    :param df: Dataframe to write to CSV file.
    :type df: :py:class:`pandas.DataFrame`

    :param str csv_file: File path and name of CSV file to write to.
    """
    df.to_csv(csv_file, index=False, date_format="%Y-%m-%d %H:%M")
    logging.info(f"wrote CSV file to {csv_file}")


@click.command(
    help="""
    Calculate and store a CSV file containing parameters of a set of random oil spills
    to drive Monte Carlo runs of MOHID.
    
    \b
    Please see 
    
    \b
    https://ubc-moad-tools.readthedocs.io/en/latest/moad_tools.html#moad_tools.midoss.random_oil_spills.cli
    
    for more information about arguments and options, and
    
    \b
    https://ubc-moad-tools.readthedocs.io/en/latest/moad_tools.html#processing-configuration-yaml-file
    
    for details of the contents of the config file.
"""
)
@click.version_option()
@click.argument("n_spills", type=int)
@click.argument(
    "config_file",
    type=click.Path(exists=True, readable=True, file_okay=True, dir_okay=False),
)
@click.argument("csv_file", type=click.Path(writable=True))
@click.option(
    "-v",
    "--verbosity",
    default="warning",
    show_default=True,
    type=click.Choice(("debug", "info", "warning", "error", "critical")),
    help="""
        Choose how much information you want to see about the progress of the calculation;
        warning, error, and critical should be silent unless something bad goes wrong. 
    """,
)
def cli(n_spills, config_file, csv_file, verbosity):
    """Command-line interface for :py:func:`moad_tools.midoss.random_oil_spills`.

    :param int n_spills: Number of spills to calculate parameters for.

    :param str config_file: File path and name of the YAML file to read processing configuration
                            dictionary from.
                            Please see :ref:`RandomOilSpillsYAMLFile` for details.

    :param str csv_file: File path and name of CSV file to write to.

    :param str verbosity: Verbosity level of logging messages about the progress of the
                          transformation.
                          Choices are :kbd:`debug, info, warning, error, critical`.
                          :kbd:`warning`, :kbd:`error`, and :kbd:`critical` should be silent
                          unless something bad goes wrong.
                          Default is :kbd:`warning`.
    """
    logging_level = getattr(logging, verbosity.upper())
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s random-oil-spills %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    df = random_oil_spills(n_spills, config_file)
    write_csv_file(df, csv_file)


# This stanza facilitates running the script in a Python debugger
if __name__ == "__main__":
    n_spills, config_file = sys.argv[1:]
    random_oil_spills(int(n_spills), config_file)
