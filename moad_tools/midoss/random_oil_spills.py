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
import logging
import sys
from datetime import timedelta
from pathlib import Path

import arrow
import click
import numpy
import pandas
import rasterio
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
    vte_probability = calc_vte_probability(geotiffs_dir)

    # Initialize PCG-64 random number generator
    random_generator = numpy.random.default_rng(random_seed)

    start_date = arrow.get(config["start date"]).datetime
    end_date = arrow.get(config["end date"]).datetime

    spill_params = collections.defaultdict(list)
    for spill in range(n_spills):
        spill_date_hour = get_date(
            start_date, end_date, vte_probability, random_generator
        )
        spill_params["spill_date_hour"].append(spill_date_hour)
        spill_params["run_days"].append(7)
        lats, lons, x_index, y_index, data_out = get_lat_lon_indices(
            geotiffs_dir,
            spill_date_hour.month,
            n_locations=1,
            upsample_factor=1,
            random_generator=random_generator,
        )

    df = pandas.DataFrame(spill_params)

    return df


def calc_vte_probability(geotiffs_dir):
    """Calculate monthly spill probability weights from vessel traffic exposure (VTE)
    in AIS GeoTIFF files.

    :param geotiffs_dir: Directory path to read AIS GeoTIFF files from.
    :type geotiffs_dir: :py:class:`pathlib.Path`

    :return: 12 elements array of monthly spill probability weights
    :rtype: :py:class:`numpy.ndarray`
    """
    total_vte_by_month = numpy.empty(12)

    for month in range(1, 13):
        # The filenames are formated as "all_2018_MM.tif"
        f_name = geotiffs_dir / f"all_2018_{month:02d}.tif"

        # open GeoTIFF file for reading
        traffic_reader = rasterio.open(f_name)

        # load data in a way that automatically closes file when finished
        with traffic_reader as dataset:
            # resample data to target shape
            data = dataset.read(1)

            # remove no-data values and singular dimension
            data = numpy.squeeze(data)
            data[data < 0] = 0

            total_vte_by_month[month - 1] = data.sum()

    # calculate VTE probability by month based on total traffic for each month
    vte_probability = total_vte_by_month / numpy.sum(total_vte_by_month)

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


def truncate(f, n):
    """Truncates/pads a float f to n decimal places without rounding"""
    s = "{}".format(f)
    if "e" in s or "E" in s:
        return "{0:.{1}f}".format(f, n)
    i, p, d = s.partition(".")
    return ".".join([i, (d + "0" * n)[:n]])


def get_lat_lon_indices(
    geotiff_directory, spill_month, water_mask, mesh, random_generator
):
    """
    :param random_generator: PCG-64 random number generator
    :type random_generator: :py:class:`numpy.random.Generator`
    """
#    print("Randomly selecting spill location from all-traffic GeoTIFF:")

    dataset = rasterio.open(
        geotiff_directory / f"all_2018_{spill_month:02.0f}.tif"
    )

    data = dataset.read(1)

    # remove no-data values
    data[data < 0] = 0

    # remove any non-water or outside domain points
    data = data * water_mask

    # calculate upsampled probability of traffic by VTE in given month
    probability_distribution = data / data.sum()

    # use 'choice' function to randomly select a geotif box, note mp is index of    # flattened array
    mp = random_generator.choice(data.shape[0]*data.shape[1], 1,
                                     p=probability_distribution.flatten())[0]
    # find indices of 2-D array
    px = int(numpy.floor(mp/data.shape[1]))
    py = mp - px * data.shape[1]

    # find lat and lon of lower right and upper left corners of the chosen box
    llx, lly = rasterio.transform.xy(dataset.transform,
                                       px+0.5, py-0.5)
    urx, ury = rasterio.transform.xy(dataset.transform,
                                       px-0.5, py+0.5)

    # find the SalishSeaCast water points in the box
    inner_points = (numpy.where(mesh.glamt[0] > llx, 1, 0) *
                numpy.where(mesh.glamt[0] < urx, 1, 0) *
               numpy.where(mesh.gphit[0] > lly, 1, 0) *
                numpy.where(mesh.gphit[0] < ury, 1, 0) *
                numpy.where(mesh.tmask[0, 0] == 1, 1, 0))

    # choose one of those water points and its lat and lon
    ssp = random_generator.choice(mesh.tmask.shape[2]*mesh.tmask.shape[3], 1,
                              p=inner_points.flatten()/inner_points.sum())
    sslon = numpy.array(mesh.glamt[0]).flatten()[ssp]
    sslat = numpy.array(mesh.gphit[0]).flatten()[ssp]

    # define nine points in the SalishSeaCast grid cell (this should be moved)
    one_third = 0.333
    within_box = {'center': [0, 0],
             'left': [one_third, 0],
             'uleft': [one_third, one_third],
             'upper' : [0, one_third],
             'uright' : [-one_third, one_third],
             'right' : [-one_third, 0],
             'lright' : [-one_third, -one_third],
             'lower' : [0, -one_third],
             'lleft' : [one_third, -one_third]}

    # chose one of those nine
    shift = (random_generator.choice(list(within_box.keys()), 1))[0]

    # calculate the grid size in lat lon
    width = mesh.tmask.shape[3]
    londx, latdx = ((numpy.array(mesh.glamt[0]).flatten()[ssp+1] -
                         numpy.array(mesh.glamt[0]).flatten()[ssp])[0],
        (numpy.array(mesh.gphit[0]).flatten()[ssp+1] -
             numpy.array(mesh.gphit[0]).flatten()[ssp])[0])
    londy, latdy = ((numpy.array(mesh.glamt[0]).flatten()[ssp+width] -
                         numpy.array(mesh.glamt[0]).flatten()[ssp])[0],
     (numpy.array(mesh.gphit[0]).flatten()[ssp+width] -
          numpy.array(mesh.gphit[0]).flatten()[ssp])[0])

    # calculate lat/lon of our spill point
    lat = sslat + latdx * within_box[shift][0] + latdy * within_box[shift][1]
    lon = sslon + londx * within_box[shift][0] + londy * within_box[shift][1]

    return lat, lon, px, py, data[px, py]


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
    logging.info(f"write CSV file to {csv_file}")


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
