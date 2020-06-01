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
import random
import sys
from array import array
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

    :rtype: :py:class:`pandas.DataFrame`
    """
    with Path(config_file).open("rt") as f:
        config = yaml.safe_load(f)
        logging.info(f"read config dict from {config_file}")
    start_date = arrow.get(config["start date"]).datetime
    end_date = arrow.get(config["end date"]).datetime
    geotiffs_dir = config["geotiffs dir"]
    spill_date_hour = get_date(start_date, end_date, geotiffs_dir)


def get_date(start_date, end_date, geotiff_directory):
    # Load GeoTIFF files for each month and add up VTE
    months = array("i", range(1, 13))
    total_vte_by_month = []

    for month in months:
        # The filenames are formated as "all_2018_MM.tif"
        f_name = f"{geotiff_directory}all_2018_{month:02.0f}.tif"

        # open GeoTIFF file for reading
        traffic_reader = rasterio.open(f_name)

        # load data in a way that automatically closes file when finished
        with traffic_reader as dataset:
            # resample data to target shape
            data = dataset.read(1)

            # remove no-data values and singular dimension
            data = numpy.squeeze(data)
            data[data < 0] = 0

            total_vte_by_month.append(data.sum())

    # calculate VTE probability by month based on total traffic for each month
    vte_probability = total_vte_by_month / numpy.sum(total_vte_by_month)

    # Randomly select month based on weighting by vessel traffic
    month_random = numpy.random.choice(months, p=vte_probability)

    # Now that month is selected, we need to choose day, year, and time.  We weight these all the same
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

    return random.choice(date_arr_select)


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
