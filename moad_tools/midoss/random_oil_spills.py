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

    oil_attribution_file = Path(config["oil attribution"])

    marine_transport_data_dir = oil_attribution_file.parent

    with oil_attribution_file.open("rt") as f:
        oil_attrs = yaml.safe_load(f)

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
        spill_params["vessel_type"].append(vessel_type)

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

        fuel_capacity, cargo_capacity = get_oil_capacity(
            oil_attrs, vessel_len, vessel_type, random_generator
        )

        fuel_spill = fuel_or_cargo_spill(oil_attrs, vessel_type, random_generator)
        max_spill_volume = fuel_capacity if fuel_spill else cargo_capacity
        spill_params["spill_volume"].append(
            max_spill_volume * choose_fraction_spilled(random_generator)
        )
        spill_params["fuel_cargo"].append("fuel" if fuel_spill else "cargo")

        vessel_fuel_types_file = Path(oil_attrs["files"]["fuel"]).name
        with (marine_transport_data_dir / vessel_fuel_types_file).open("rt") as f:
            vessel_fuel_types = yaml.safe_load(f)
        oil_type = get_oil_type(
            oil_attrs,
            vessel_type,
            vessel_origin,
            vessel_dest,
            fuel_spill,
            vessel_fuel_types,
            marine_transport_data_dir,
            random_generator,
        )
        spill_params["Lagrangian_template"].append(f"Lagrangian_{oil_type}.dat")

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
             * origin of AIS track from which spill occurs (str or None)
             * destination of AIS track from which spill occurs (str or None)
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

    try:
        chosen_track_index = random_generator.choice(
            range(len(ais_tracks.index)), p=vte / vte.sum()
        )
    except ValueError:
        raise ValueError(
            f"No AIS tracks in GeoTIFF box: "
            f"{shapefiles_dir=}, {vessel_type=}, {spill_month=}, {geotiff_bbox.exterior.coords.xy=}"
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


def fuel_or_cargo_spill(oil_attrs, vessel_type, random_generator):
    """Randomly choose whether the spill is from fuel or cargo volume for vessel types that
    transport oil as cargo.

    :param dict oil_attrs: Oil attribution information from the output of make_oil_attrs.py.

    :param str vessel_type: Vessel type from which spill occurs.

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Fuel or cargo spill flag.
    :rtype: boolean
    """
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
        fuel_spill = True
    return fuel_spill


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


def get_oil_type(
    oil_attrs,
    vessel_type,
    vessel_origin,
    vessel_dest,
    fuel_spill,
    vessel_fuel_types,
    marine_transport_data_dir,
    random_generator,
):
    """Randomly choose a type of oil spilled based on vessel type, AIS origin & destination,
    and whether fuel or cargo is spilled.

    :param dict oil_attrs: Oil attribution information from the output of make_oil_attrs.py.

    :param str vessel_type: Vessel type from which spill occurs.

    :param str or None vessel_origin: Origin of AIS track from which spill occurs.

    :param str or None vessel_dest: Destination of AIS track from which spill occurs.

    :param boolean fuel_spill: Fuel or cargo spill flag.

    :param dict vessel_fuel_types: Mapping of fuel types and probabilities for vessel types.

    :param marine_transport_data_dir: Directory path to marine_transport_data files repository
                                      cloned from https://github.com/MIDOSS/marine_transport_data.
    :type marine_transport_data_dir: :py:class:`pathlib.Path`

    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Type of oil spilled.
    :rtype: str
    """
    raw_fuel_type_probs = numpy.array(
        [
            vessel_fuel_types[vessel_type]["bunker"],
            vessel_fuel_types[vessel_type]["diesel"],
        ]
    )
    if abs(raw_fuel_type_probs.sum() - 1) > 1e-4:
        raise ValueError(
            f"Probable data entry error - sum of raw probabilities is not close to 1: "
            f"{raw_fuel_type_probs.sum()} for {vessel_type=}"
        )

    if fuel_spill:
        oil_type = random_generator.choice(
            ["bunker", "diesel"], p=raw_fuel_type_probs / raw_fuel_type_probs.sum(),
        )
    else:
        if vessel_type == "atb":
            oil_type = get_oil_type_atb(
                oil_attrs,
                vessel_origin,
                vessel_dest,
                marine_transport_data_dir,
                random_generator,
            )
        elif vessel_type == "barge":
            oil_type, barge_fuel_spill = get_oil_type_barge(
                oil_attrs,
                vessel_origin,
                vessel_dest,
                marine_transport_data_dir,
                random_generator,
            )
            if barge_fuel_spill:
                oil_type = random_generator.choice(
                    ["bunker", "diesel"],
                    p=raw_fuel_type_probs / raw_fuel_type_probs.sum(),
                )
        elif vessel_type == "tanker":
            oil_type = get_oil_type_tanker(
                oil_attrs,
                vessel_origin,
                vessel_dest,
                marine_transport_data_dir,
                random_generator,
            )
    return oil_type


def get_oil_type_atb(
    oil_attrs, origin, destination, transport_data_dir, random_generator
):
    """Randomly choose type of cargo oil spilled from an ATB (articulated tug and barge) based on
    AIS track origin & destination, and oil cargo attribution analysis.

    Unlike traditional tank barges, the vessels with 'atb' designation are known oil-cargo vessels.
    We used three different data sources to verify: AIS, Dept of Ecology's fuel transfer records
    and Charlie Costanzo's ATB list. Details of traffic can be seen in this google spreadsheet:
    https://docs.google.com/spreadsheets/d/1dlT0JydkFG43LorqgtHle5IN6caRYjf_3qLrUYqANDY/edit#gid=1593104354

    Because of this pre-identification and selection method, we can assume that all ATBs are
    oil-cargo atbs and that the absence of origin-destination information is due to issues in
    linking ship tracks and not ambiguity about whether traffic is oil-cargo traffic.

    :param dict oil_attrs: Oil attribution information from the output of make_oil_attrs.py.

    :param str or None origin: Origin of AIS track from which spill occurs.

    :param str or None destination: Destination of AIS track from which spill occurs.

    :param transport_data_dir: Directory path to marine_transport_data files repository
                               cloned from https://github.com/MIDOSS/marine_transport_data.
    :type transport_data_dir: :py:class:`pathlib.Path`

    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Type of oil spilled.
    :rtype: str
    """
    vessel_type = "atb"

    # Assign US and CAD origin/destinations from oil_attrs file
    CAD_origin_destination = oil_attrs["categories"]["CAD_origin_destination"]
    US_origin_destination = oil_attrs["categories"]["US_origin_destination"]

    # Get cargo oil type attribution information from oil-type yaml files
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["CAD_origin"]).name
    with yaml_file.open("rt") as f:
        CAD_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["WA_destination"]).name
    with yaml_file.open("rt") as f:
        WA_in_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["WA_origin"]).name
    with yaml_file.open("rt") as f:
        WA_out_yaml = yaml.safe_load(f)
    # # US_origin is for US as origin
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["US_origin"]).name
    with yaml_file.open("rt") as f:
        US_yaml = yaml.safe_load(f)
    # # US_combined represents the combined import and export of oil
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["US_combined"]).name
    with yaml_file.open("rt") as f:
        USall_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["Pacific_origin"]).name
    with yaml_file.open("rt") as f:
        Pacific_yaml = yaml.safe_load(f)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # NOTE: these pairs need to be used together for "get_oil_type_cargo"
    #   (but don't yet have error-checks in place):
    # - "WA_in_yaml" and "destination"
    # - "WA_out_yaml" and "origin"
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if origin in CAD_origin_destination:
        if origin == "Westridge Marine Terminal":
            if destination == "U.S. Oil & Refining":
                oil_type = get_oil_type_cargo(
                    CAD_yaml, origin, vessel_type, random_generator
                )
            elif destination in US_origin_destination:
                oil_type = get_oil_type_cargo(
                    CAD_yaml, origin, vessel_type, random_generator
                )
            elif destination in CAD_origin_destination:
                # assume export within CAD is from Jet fuel storage tanks
                # as there is a pipeline to Parkland for crude oil
                oil_type = "jet"
            else:
                oil_type = get_oil_type_cargo(
                    CAD_yaml, origin, vessel_type, random_generator
                )
        else:
            if destination in US_origin_destination:
                # we have better information on WA fuel transfers,
                # so I prioritize this information source
                oil_type = get_oil_type_cargo(
                    WA_in_yaml, destination, vessel_type, random_generator
                )
            elif destination == "ESSO Nanaimo Departure Bay":
                oil_type = get_oil_type_cargo(
                    CAD_yaml, destination, vessel_type, random_generator
                )

            elif destination == "Suncor Nanaimo":
                oil_type = get_oil_type_cargo(
                    CAD_yaml, destination, vessel_type, random_generator
                )
            else:
                oil_type = get_oil_type_cargo(
                    CAD_yaml, origin, vessel_type, random_generator
                )
    elif origin in US_origin_destination:
        if destination == "Westridge Marine Terminal":
            # Westridge stores jet fuel from US for re-distribution
            oil_type = "jet"
        else:
            oil_type = get_oil_type_cargo(
                WA_out_yaml, origin, vessel_type, random_generator
            )
    elif destination in US_origin_destination:
        oil_type = get_oil_type_cargo(
            WA_in_yaml, destination, vessel_type, random_generator
        )
    elif destination in CAD_origin_destination:
        if destination == "Westridge Marine Terminal":
            # Westridge doesn't receive crude for storage
            oil_type = "jet"
        else:
            oil_type = get_oil_type_cargo(
                CAD_yaml, destination, vessel_type, random_generator
            )
    elif origin == "Pacific":
        oil_type = get_oil_type_cargo(
            Pacific_yaml, origin, vessel_type, random_generator
        )
    elif origin == "US":
        oil_type = get_oil_type_cargo(US_yaml, origin, vessel_type, random_generator)
    else:
        # For all other traffic, use a generic fuel attribution from the combined
        # US import and export
        oil_type = get_oil_type_cargo_generic_US(
            USall_yaml, vessel_type, random_generator
        )

    return oil_type


def get_oil_type_barge(
    oil_attrs, origin, destination, transport_data_dir, random_generator
):
    """Randomly choose type of cargo oil spilled from abarge based on AIS track
    origin & destination, and oil cargo attribution analysis.

    Decision tree for allocating oil type to barge traffic see Google drawing
    [Barge_Oil_Attribution](https://docs.google.com/drawings/d/10PM53-UnnILYCAPKU9MxiR-Y4OW0tIMhVzSjaHr-iSc/edit)
    for a visual representation.

    :param dict oil_attrs: Oil attribution information from the output of make_oil_attrs.py.

    :param str or None origin: Origin of AIS track from which spill occurs.

    :param str or None destination: Destination of AIS track from which spill occurs.

    :param transport_data_dir: Directory path to marine_transport_data files repository
                               cloned from https://github.com/MIDOSS/marine_transport_data.
    :type transport_data_dir: :py:class:`pathlib.Path`

    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: 2-tuple composed of:

             * Type of oil spilled (str or None)
             * Fuel or cargo spill flag (boolean)

    :rtype: tuple
    """
    vessel_type = "barge"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Set 'fuel_spill'
    #
    # Fuel_spill is used to flag ship tracks with barge designation
    # as non-oil cargo traffic with, hence, fuel-spill risk only
    # instead of combined cargo- & fuel-spill risk.
    #
    # This flag will turn to True (fuel-spill risk only) when:
    # 1) Tug is not included in Casey's pre-selected "Voyage" dataset,
    #    which selected tug traffic that traveled within a 2 km of
    #    known marine oil terminal at some point in 2018.  If not
    #    included, the origin/destination values are null.
    # 2) Tug is included in Casey's pre-selected data but is not
    #    joined by our origin-destination analysis and, as a result,
    #    has null values for origin/destination.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    fuel_spill = False

    # Assign US and CAD origin/destinations from oil_attrs file
    CAD_origin_destination = oil_attrs["categories"]["CAD_origin_destination"]
    US_origin_destination = oil_attrs["categories"]["US_origin_destination"]

    # Get cargo oil type attribution information from oil-type yaml files
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["CAD_origin"]).name
    with yaml_file.open("rt") as f:
        CAD_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["WA_destination"]).name
    with yaml_file.open("rt") as f:
        WA_in_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["WA_origin"]).name
    with yaml_file.open("rt") as f:
        WA_out_yaml = yaml.safe_load(f)
    # # US_origin is for US as origin
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["US_origin"]).name
    with yaml_file.open("rt") as f:
        US_yaml = yaml.safe_load(f)
    # # US_combined represents the combined import and export of oil
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["US_combined"]).name
    with yaml_file.open("rt") as f:
        USall_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["Pacific_origin"]).name
    with yaml_file.open("rt") as f:
        Pacific_yaml = yaml.safe_load(f)

    # get probability of non-allocated track being an oil-barge
    probability_oilcargo = oil_attrs["vessel_attributes"]["barge"][
        "probability_oilcargo"
    ]
    probability_fuelonly = 1 - probability_oilcargo

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # these pairs need to be used together for "get_oil_type_cargo"
    # (but don't yet have error-checks in place):
    # - "WA_in_yaml" and "destination"
    # - "WA_out_yaml" and "origin"
    #
    # ERROR CATCH for case of no oil transfer for given selection of
    # yaml file, origin, and vessel_type is currently to set flag to fuel
    # spill potential and not cargo spill potential
    #
    # Why?
    #
    # Because there are lots of tugs that are not associated
    # with oil tank barges. We do our best to identify oil cargo and
    # then need to rely on a probability of oil cargo informed by AIS
    # traffic data.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if origin in CAD_origin_destination:
        if origin == "Westridge Marine Terminal":
            if destination in CAD_origin_destination:
                oil_type = "jet"
            else:
                # allocate oil type based on a 'barge' from Westridge
                oil_type = get_oil_type_cargo(
                    CAD_yaml, origin, vessel_type, random_generator
                )
        else:
            if destination in US_origin_destination:
                # we have better information on WA fuel transfers,
                # so I'm prioritizing this information source

                oil_type = get_oil_type_cargo(
                    WA_in_yaml, destination, vessel_type, random_generator
                )

                # There is a possibility that barge traffic has a CAD
                # origin but the US destination is matched with no fuel
                # transport.  It's not likely; but a possibility. This
                # is an error catch for if there is no fuel-type
                # associated with a barge import to WA destination.
                # sum(probability) == 0 will return empty oil type

                # *** ERROR CATCH ***
                if not oil_type:
                    fuel_spill = True
                    oil_type = None
                # *** END ERROR CATCH ***

            elif destination == "ESSO Nanaimo Departure Bay":
                # These are fixed to have a oil type option for all
                # vessel types.  No error catch needed.
                # See CAD_origin.yaml for verification.

                oil_type = get_oil_type_cargo(
                    CAD_yaml, destination, vessel_type, random_generator
                )

            elif destination == "Suncor Nanaimo":
                # Similar to ESSO. No error catch needed.

                oil_type = get_oil_type_cargo(
                    CAD_yaml, destination, vessel_type, random_generator
                )

            else:
                # if origin is a CAD terminal with no US oil terminal
                # destination and no destination to a better known
                # CAD terminal then just use the CAD origin allocation
                # An option here is to flag a destination of 'Pacific'
                # or 'US' and use US fuel alloction. I didn't see a
                # compelling case for adding this complexity, so I kept
                # it simple.  Similar to ESSO, above, no error catch
                # needed.

                oil_type = get_oil_type_cargo(
                    CAD_yaml, origin, vessel_type, random_generator
                )

    elif origin in US_origin_destination:
        oil_type = get_oil_type_cargo(
            WA_out_yaml, origin, vessel_type, random_generator
        )

        # *** ERROR CATCH ***
        # As a result of using 2 different data sources (AIS and
        # Ecology), there is a chance that AIS has origin from a
        # marine terminal for which no barge transfers are recorded
        # in the DOE database.  For this unlikely but possible case,
        # I attribute the barge in a way that is consistent with the
        # DOE database by allocating the barge as a non-oil cargo barge
        # that will pose a fuel-oil spill risk only.
        if not oil_type:
            fuel_spill = True
            oil_type = None
        # *** END ERROR CATCH ***

    elif destination in US_origin_destination:
        oil_type = get_oil_type_cargo(
            WA_in_yaml, destination, vessel_type, random_generator
        )

        # *** ERROR CATCH ***
        # Same explanation as given above, in
        # 'elif origin in US_origin_destination'
        if not oil_type:
            fuel_spill = True
            oil_type = None
        # *** END ERROR CATCH ***

    elif destination in CAD_origin_destination:
        if destination == "Westridge Marine Terminal":
            # Westridge doesn't receive crude for storage
            oil_type = "jet"
        else:
            oil_type = get_oil_type_cargo(
                CAD_yaml, destination, vessel_type, random_generator
            )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Remaining cases are those that were not linked to an oil terminal
    # in our origin-destination analysis for transport to/from
    # known oil-transfer facilities.  Tracks were not joined (and will
    # have null values for origin/destination) if adjacent
    # ship tracks are (a) < 1 km long, (b) over 4 hours apart, (c)
    # requiring > 80 knts to join.  The tracks that lack details of
    # origin-destination fall into the category of ship tracks that
    # may or may not be oil-traffic.  As such, I first use probability
    # of oil-cargo for tank barge traffic to
    # weight whether the ship track represents an oil-carge & fuel spill
    # risk (fuel_spill = False) or a fuel-spill risk only (fuel_spill = True).
    # For the cases in which fuel_spill is False, I use origin
    # as 'US','Pacific' or 'Canada' to specify cargo allocation
    # NOTE: Currently Canada == US
    # ALSO NOTE: Once the tracks that are identified as potential
    # cargo-spill tracks (fuel_spill = False), they will still be treated
    # like any other tank traffic with an .8/.2 probility of
    # cargo/fuel spill.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    elif origin == "Pacific":
        fuel_spill = random_generator.choice(
            [False, True], p=[probability_oilcargo, probability_fuelonly]
        )
        if fuel_spill:
            oil_type = None
        else:
            oil_type = get_oil_type_cargo_generic_US(
                Pacific_yaml, vessel_type, random_generator
            )
    elif origin == "US":
        fuel_spill = random_generator.choice(
            [False, True], p=[probability_oilcargo, probability_fuelonly]
        )
        if fuel_spill:
            oil_type = None
        else:
            oil_type = get_oil_type_cargo_generic_US(
                US_yaml, vessel_type, random_generator
            )
    elif origin == "Canada":
        fuel_spill = random_generator.choice(
            [False, True], p=[probability_oilcargo, probability_fuelonly]
        )
        if fuel_spill:
            oil_type = None

        else:
            oil_type = get_oil_type_cargo_generic_US(
                US_yaml, vessel_type, random_generator
            )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Remaining cases have null values for origin destination.
    # I first use probability of oil-cargo for tank barge traffic to
    # weight whether the ship track is an oil-carge & fuel spill risk
    # (fuel_spill = False) or a fuel-spill risk only (fuel_spill = True)
    # For the cases in which fuel_spill is False, I use the US_generic fuel allocation
    # to attribute fuel type.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    else:
        fuel_spill = random_generator.choice(
            [False, True], p=[probability_oilcargo, probability_fuelonly]
        )
        if fuel_spill:
            oil_type = None
        else:
            oil_type = get_oil_type_cargo_generic_US(
                US_yaml, vessel_type, random_generator
            )

    return oil_type, fuel_spill


def get_oil_type_tanker(
    oil_attrs, origin, destination, transport_data_dir, random_generator
):
    """Randomly choose type of cargo oil spilled from a tanker based on AIS track
    origin & destination, and oil cargo attribution analysis.

    Decision tree for allocating oil type to tanker traffic see Google drawing
    [Tanker_Oil_Attribution](https://docs.google.com/drawings/d/1-4gl2yNNWxqXK-IOr4KNZxO-awBC-bNrjRNrt86fykU/edit)
    for a visual representation.

    :param dict oil_attrs: Oil attribution information from the output of make_oil_attrs.py.

    :param str or None origin: Origin of AIS track from which spill occurs.

    :param str or None destination: Destination of AIS track from which spill occurs.

    :param transport_data_dir: Directory path to marine_transport_data files repository
                               cloned from https://github.com/MIDOSS/marine_transport_data.
    :type transport_data_dir: :py:class:`pathlib.Path`

    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Type of oil spilled.
    :rtype: str
    """
    vessel_type = "tanker"

    # Assign US and CAD origin/destinations from oil_attrs file
    CAD_origin_destination = oil_attrs["categories"]["CAD_origin_destination"]
    US_origin_destination = oil_attrs["categories"]["US_origin_destination"]

    # Get cargo oil type attribution information from oil-type yaml files
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["CAD_origin"]).name
    with yaml_file.open("rt") as f:
        CAD_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["WA_destination"]).name
    with yaml_file.open("rt") as f:
        WA_in_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["WA_origin"]).name
    with yaml_file.open("rt") as f:
        WA_out_yaml = yaml.safe_load(f)
    # # US_origin is for US as origin
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["US_origin"]).name
    with yaml_file.open("rt") as f:
        US_yaml = yaml.safe_load(f)
    # # US_combined represents the combined import and export of oil
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["US_combined"]).name
    with yaml_file.open("rt") as f:
        USall_yaml = yaml.safe_load(f)
    yaml_file = transport_data_dir / Path(oil_attrs["files"]["Pacific_origin"]).name
    with yaml_file.open("rt") as f:
        Pacific_yaml = yaml.safe_load(f)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # NOTE: these pairs need to be used together for
    # "get_oil_type_cargo" (but don't yet have error-checks in place):
    # - "WA_in_yaml" and "destination"
    # - "WA_out_yaml" and "origin"
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if origin in CAD_origin_destination:
        if origin == "Westridge Marine Terminal":
            oil_type = get_oil_type_cargo(
                CAD_yaml, origin, vessel_type, random_generator
            )
        else:
            if destination in US_origin_destination:
                # we have better information on WA fuel transfers,
                # so I'm prioritizing this information source
                oil_type = get_oil_type_cargo(
                    WA_in_yaml, destination, vessel_type, random_generator
                )
            else:
                oil_type = get_oil_type_cargo(
                    CAD_yaml, origin, vessel_type, random_generator
                )
    elif origin in US_origin_destination:
        oil_type = get_oil_type_cargo(
            WA_out_yaml, origin, vessel_type, random_generator
        )
    elif destination in US_origin_destination:
        oil_type = get_oil_type_cargo(
            WA_in_yaml, destination, vessel_type, random_generator
        )
    elif destination in CAD_origin_destination:
        oil_type = get_oil_type_cargo(
            CAD_yaml, destination, vessel_type, random_generator
        )
    elif origin == "Pacific":
        oil_type = get_oil_type_cargo_generic_US(
            Pacific_yaml, vessel_type, random_generator
        )
    elif origin == "US":
        oil_type = get_oil_type_cargo_generic_US(US_yaml, vessel_type, random_generator)
    else:
        # Currently, this is a catch for all ship tracks not allocated with origin or destination
        # It's a generic fuel attribution from the combined US import and export
        oil_type = get_oil_type_cargo_generic_US(
            USall_yaml, vessel_type, random_generator
        )

    return oil_type


def get_oil_type_cargo(cargo_info, facility, vessel_type, random_generator):
    """Randomly choose cargo oil type based on facility and vessel type
    by querying information in input yaml_file.

    :param dict cargo_info: Cargo oil type attribution information from the output of a
                            make_cargo_*.ipynb notebooks.

    :param str facility: Vessel origin from AIS.

    :param str vessel_type: Vessel type from which spill occurs.

    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Cargo oil type.
    :rtype: str
    """
    ship = cargo_info[facility][vessel_type]
    raw_probs = numpy.array([ship[oil_type]["fraction_of_total"] for oil_type in ship])
    if abs(raw_probs.sum() - 1) > 1e-4:
        raise ValueError(
            f"Probable data entry error - sum of raw probabilities is not close to 1: "
            f"{raw_probs.sum()} for {cargo_info=}, {facility=}, {vessel_type=}"
        )
    oil_type = random_generator.choice(list(ship.keys()), p=raw_probs / raw_probs.sum())
    return oil_type


def get_oil_type_cargo_generic_US(cargo_info, vessel_type, random_generator):
    """Returns oil for cargo attribution based on facility and vessel by querying information
    in input yaml_file.

    This is essentially the same as 'get_oil_type_cargo' but is designed for yaml files
    that lack facility names.

    :param dict cargo_info: Cargo oil type attribution information from the output of the
                            make_cargo_AllUS.ipynb notebook.

    :param str vessel_type: Vessel type from which spill occurs.

    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Cargo oil type.
    :rtype: str
    """
    ship = cargo_info[vessel_type]
    raw_probs = numpy.array([ship[fuel]["fraction_of_total"] for fuel in ship])
    if abs(raw_probs.sum() - 1) > 1e-4:
        raise ValueError(
            f"Probably data entry error - sum of raw probabilities is not close to 1: "
            f"{raw_probs.sum()} for {vessel_type=}, {cargo_info=}"
        )
    oil_type = random_generator.choice(list(ship.keys()), p=raw_probs / raw_probs.sum())
    return oil_type


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
    logging.getLogger("fiona").setLevel(logging.WARNING)
    logging.getLogger("rasterio").setLevel(logging.WARNING)
    df = random_oil_spills(n_spills, config_file)
    write_csv_file(df, csv_file)


# This stanza facilitates running the script in a Python debugger
if __name__ == "__main__":
    n_spills, config_file = sys.argv[1:]
    random_oil_spills(int(n_spills), config_file)
