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

        spill_lat, spill_lon, geotiff_x_index, geotiff_y_index, _ = get_lat_lon_indices(
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

        search_radius = 0.5  # km
        vessel_len, vessel_origin, vessel_dest = get_length_origin_destination(
            shapefiles_dir,
            vessel_type,
            spill_date_hour.month,
            spill_lat,
            spill_lon,
            search_radius,
            random_generator,
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

    :return: 5-tuple composed of:

             * spill latitude [°N in [-90°, 90°] range]
             * spill longitude [°E in [-180°, 180°] range]
             * x-index of GeoTIFF cell in which spill is located
             * y-index of GeoTIFF cell in which spill is located
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
        llx, lly = rasterio.transform.xy(dataset.transform, px + 0.5, py - 0.5)
        urx, ury = rasterio.transform.xy(dataset.transform, px - 0.5, py + 0.5)

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

        return lat, lon, px, py, data[px, py]


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

    :return: Randomly selected vessel type from which spill occurs
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

    # Choose a randome vessel type, weighted by the vessel type VTE probability distribution
    # for the month
    probability = vte_by_vessel_type / vte_by_vessel_type.sum()
    vessel_type = random_generator.choice(vessel_types, p=probability)

    return vessel_type


def get_length_origin_destination(
    shapefiles_dir,
    vessel_type,
    spill_month,
    spill_lat,
    spill_lon,
    search_radius,
    random_generator,
):
    """

    :param shapefiles_dir: Directory path to read shapefiles from
    :type shapefiles_dir: :py:class:`pathlib.Path`

    :param str vessel_type: Vessel type from which spill occurs.

    :param int spill_month: Month number for which to choose a spill location.

    :param float spill_lat: Spill latitude [°N in [-90°, 90°] range].

    :param float spill_lon: Spill longitude [°E in [-180°, 180°] range].

    :param float search_radius:

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return:
    """
    # load data
    vessel_type_spill_month = f"{vessel_type}_2018_{spill_month:02d}"
    shapefile = (
        shapefiles_dir / vessel_type_spill_month / f"{vessel_type_spill_month}.shp"
    )
    data = geopandas.read_file(shapefile)
    nrows, ncols = data.shape

    # think about a way of doing this that doesn't require
    # loading all lat/lon values (with a healthy dose of patience)
    logging.info("this is going to take a minute....")
    lon_array = [data.geometry[i].coords[0][0] for i in range(nrows)]
    lat_array = [data.geometry[i].coords[0][1] for i in range(nrows)]

    # identify all the lines within search_radius
    distance = _haversine(spill_lon, spill_lat, lon_array, lat_array)
    array_index = numpy.where(distance < search_radius)

    total_seconds = numpy.zeros(len(array_index))
    total_distance = numpy.zeros(len(array_index))
    vte = numpy.zeros(len(array_index))

    # loop through values in array_index values to calculate
    for index in range(len(array_index)):
        # calculate the duration of travel for each poly line segment
        start_date = datetime.datetime.strptime(
            data.ST_DATE[index], "%Y-%m-%d %H:%M:%S"
        )
        end_date = datetime.datetime.strptime(data.EN_DATE[index], "%Y-%m-%d %H:%M:%S")
        delta_time = end_date - start_date
        total_seconds[index] = delta_time.total_seconds()

        # calculate the distance of each poly line
        start_lon = data.geometry[index].coords[0][0]
        start_lat = data.geometry[index].coords[0][1]
        end_lon = data.geometry[index].coords[1][0]
        end_lat = data.geometry[index].coords[1][1]

        # calculate the distance in km of vessel line segment
        total_distance[index] = _haversine(start_lon, start_lat, end_lon, end_lat)
        vte[index] = total_seconds[index] / total_distance[index]

    # find the index for greatest vte (for cases where there is
    # more than one polyline)
    (i,) = numpy.where(vte == max(vte))
    the_one = array_index[i.item()]

    # now that we have found the one true polyline, lets get its digits!
    length = data.LENGTH[the_one.item()]
    origin = data.FROM_[the_one.item()]
    destination = data.TO[the_one.item()]

    # standardize ATB and tug lengths to represent length of tug and tank barge
    # see [AIS data attribute table](https://docs.google.com/document/d/14hAxrTFpKloy88zRYLL4TiqLwbn8s53MYQeCt6B3MJ4/edit)
    # for more information
    if vessel_type == "barge" or vessel_type == "atb" and length < 100:
        length = random_generator.choice([147, 172, 178, 206, 207])

    # that's a wrap, folks.
    return length, origin, destination


def _haversine(lon1, lat1, lon2, lat2):
    """Calculate the great-circle distance in kilometers between two points
    on a sphere from their longitudes and latitudes.

    Reference: http://www.movable-type.co.uk/scripts/latlong.html

    :arg lon1: Longitude of point 1.
    :type lon1: float or :py:class:`numpy.ndarray`

    :arg lat1: Latitude of point 1.
    :type lat1: float or :py:class:`numpy.ndarray`

    :arg lon2: Longitude of point 2.
    :type lon2: float or :py:class:`numpy.ndarray`

    :arg lat2: Latitude of point 2.
    :type lat2: float or :py:class:`numpy.ndarray`

    :returns: Great-circle distance between two points in km
    :rtype: float or :py:class:`numpy.ndarray`
    """
    lon1, lat1, lon2, lat2 = map(numpy.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        numpy.sin(dlat / 2) ** 2
        + numpy.cos(lat1) * numpy.cos(lat2) * numpy.sin(dlon / 2) ** 2
    )
    c = 2 * numpy.arcsin(numpy.sqrt(a))
    km = 6367 * c
    return km


def choose_fraction_spilled(random_generator):
    """Randomly choose a fraction spilled based on the _cumulative_spill_fraction() fit.

    :param random_generator: PCG-64 random number generator.
    :type random_generator: :py:class:`numpy.random.Generator`

    :return: Fraction of oil colume spilled.
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
