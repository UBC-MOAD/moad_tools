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
"""Functions and command-line tool to calculate and store a Numpy array file containing
a SalishSeaCast domain water mask for the AIS ship track density GeoTIFF files used to
generate oil spill parameters for Monte Carlo runs of MOHID.
"""
import logging
import sys
from pathlib import Path

import click
import numpy
import rasterio
import xarray

logging.getLogger(__name__).addHandler(logging.NullHandler())


def geotiff_watermask(geotiff_file, meshmask_file):
    """Calculate a Numpy boolean array containing a SalishSeaCast domain water mask for the
    AIS ship track density GeoTIFF files used to generate oil spill parameters for
    Monte Carlo runs of MOHID.

    :param str geotiff_file: File path and name of an AIS ship tracks GeoTIFF file to use the
                             pixel lons/lats from to calculate water mask;
                             typically a ShipTrackDensityGeoTIFFs/all_yyyy_mm.tif file.

    :param str meshmask_file: File path and name of a SalishSeaCast NEMO mesh mask file to use
                              the NEMO grid lons/lats and T-grid water/land maks from to
                              calculate the water mask.

    :return: Boolean water mask to apply to AIS ship track density GeoTIFF files to restrict
             them to the SalishSeaCast NEMO domain.
    :rtype: :py:class:`numpy.ndarray`
    """
    geotiff_path = Path(geotiff_file).resolve()
    meshmask_path = Path(meshmask_file).resolve()
    with rasterio.open(geotiff_path) as ais_density:
        logging.info(f"opened AIS ship tracks GeoTIFF: {geotiff_path}")
        with xarray.open_dataset(meshmask_path) as ssc_mesh:
            logging.info(f"opened SalishSeaCast NEMO mesh mask: {meshmask_path}")
            return calc_watermask(ais_density, ssc_mesh)


def calc_watermask(ais_density, ssc_mesh):
    """Calculate a Numpy boolean array containing a SalishSeaCast domain water mask for the
    AIS ship track density GeoTIFF files used to generate oil spill parameters for
    Monte Carlo runs of MOHID.

    :param ais_density: AIS ship tracks GeoTIFF object to use the pixel lons/lats from
                        to calculate water mask.
    :type ais_density: :py:class:`rasterio.io.DatasetReader`

    :param ssc_mesh: SalishSeaCast NEMO mesh mask dataset to use the NEMO grid lons/lats
                     and T-grid water/land maks from to calculate the water mask.
    :type ssc_mesh: :py:class:`xarray.Dataset`

    :return: Boolean water mask to apply to AIS ship track density GeoTIFF files to restrict
             them to the SalishSeaCast NEMO domain.
    :rtype: :py:class:`numpy.ndarray`
    """
    n_x, n_y = ais_density.shape
    watermask = numpy.full(ais_density.shape, False, dtype=bool)
    logging.info("Calculating water mask...")
    for xx in range(n_x):
        for yy in range(n_y):
            # The rasterio.transform.xy() type annotations say that the 2nd & 3rd args
            # should be Union(list, int), but floats seem to work just fine.
            llx, lly = rasterio.transform.xy(ais_density.transform, xx + 0.5, yy - 0.5)
            urx, ury = rasterio.transform.xy(ais_density.transform, xx - 0.5, yy + 0.5)

            watermask[xx, yy] = numpy.any(
                numpy.logical_and(
                    ssc_mesh.tmask.isel(t=0, z=0),
                    numpy.logical_and(
                        numpy.logical_and(
                            ssc_mesh.glamt.isel(t=0) > llx,
                            ssc_mesh.glamt.isel(t=0) < urx,
                        ),
                        numpy.logical_and(
                            ssc_mesh.gphit.isel(t=0) > lly,
                            ssc_mesh.gphit.isel(t=0) < ury,
                        ),
                    ),
                )
            )
    return watermask


def write_numpy_file(watermask, numpy_file):
    """Store a Numpy array file containing a boolean water mask to apply to
    AIS ship track density GeoTIFF files to restrict them to the SalishSeaCast NEMO domain.

    :param watermask: Boolean water mask to apply to AIS ship track density GeoTIFF files
                      to restrict them to the SalishSeaCast NEMO domain.
    :type watermask: :py:class:`numpy.ndarray`

    :param str numpy_file: File path and name of Numpy array file to write the water mask to.
    """
    numpy_path = Path(numpy_file).resolve()
    numpy.save(numpy_path, watermask, allow_pickle=False, fix_imports=False)
    logging.info(f"wrote Numpy boolean water mask array to: {numpy_path}")


@click.command(
    help="""
    Calculate and store a Numpy array file containing a SalishSeaCast domain water mask for the 
    AIS ship track density GeoTIFF files used to generate oil spill parameters for 
    Monte Carlo runs of MOHID.

    \b
    Please see 
    
    \b
    https://ubc-moad-tools.readthedocs.io/en/latest/moad_tools.html#moad_tools.midoss.geotiff_watermask.cli
    
    for more information about arguments and options.
    """
)
@click.version_option()
@click.argument(
    "geotiff_file",
    type=click.Path(exists=True, readable=True, file_okay=True, dir_okay=False),
)
@click.argument(
    "meshmask_file",
    type=click.Path(exists=True, readable=True, file_okay=True, dir_okay=False),
)
@click.argument("numpy_file", type=click.Path(writable=True))
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
def cli(geotiff_file, meshmask_file, numpy_file, verbosity):
    """Command-line interface for :py:func:`moad_tools.midoss.geotiff_watermask`.

    :param str geotiff_file: File path and name of an AIS ship tracks GeoTIFF file to use the
                             pixel lons/lats from to calculate water mask;
                             typically a ShipTrackDensityGeoTIFFs/all_yyyy_mm.tif file.

    :param str meshmask_file: File path and name of a SalishSeaCast NEMO mesh mask file to use
                              the NEMO grid lons/lats and T-grid water/land maks from to
                              calculate the water mask.

    :param str numpy_file: File path and name of Numpy array file to write the water mask to.

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
        format="%(asctime)s geotiff-watermask %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    watermask = geotiff_watermask(geotiff_file, meshmask_file)
    write_numpy_file(watermask, numpy_file)


# This stanza facilitates running the script in a Python debugger
if __name__ == "__main__":
    geotiff_file, meshmask_file = sys.argv[1:]
    geotiff_watermask(geotiff_file, meshmask_file)
