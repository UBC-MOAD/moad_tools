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
from pathlib import Path

import click
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
