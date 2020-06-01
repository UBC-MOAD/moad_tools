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
import logging
import sys
from datetime import timedelta
from pathlib import Path

import arrow
import click
import numpy
import rasterio
import yaml

logging.getLogger(__name__).addHandler(logging.NullHandler())


def random_oil_spills(n_spills, config_file):
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

    geotiffs_dir = Path(config["geotiffs dir"])
    vte_probability = calc_vte_probability(geotiffs_dir)

    # Initialize PCG-64 random number generator
    random_generator = numpy.random.default_rng(random_seed)

    start_date = arrow.get(config["start date"]).datetime
    end_date = arrow.get(config["end date"]).datetime

    spill_date_hour = get_date(start_date, end_date, vte_probability, random_generator)


def calc_vte_probability(geotiffs_dir):
    """Calculate monthly spill probability weights from vessel traffic exposure (VTE)
    in AIS GeoTIFF files.

    :param geotiffs_dir: File path to read AIS GeoTIFF files from.
    :type geotiffs_dir: :py:class:`pathlib.Path`

    :return: 12 elements array of monthly spill probability weights
    :rtype: :py:class:`numpy.ndarray`
    """
    # Load GeoTIFF files for each month and add up VTE
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

    :param start_date: Starting date of period in which spill dates and hours are to be selected.
    :type start_date: :py:class:`datetime.datetime`

    :param end_date: Ending date of period in which spill dates and hours are to be selected.
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


def write_csv_file(df, csv_file):
    """
    :param df: Dataframe to write to CSV file.
    :type df: :py:class:`pandas.DataFrame`

    :param str csv_file: File path and name of CSV file to write to.
    """
    pass


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
